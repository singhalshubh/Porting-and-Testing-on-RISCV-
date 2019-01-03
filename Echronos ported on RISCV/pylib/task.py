#
# eChronos Real-Time Operating System
# Copyright (c) 2017, Commonwealth Scientific and Industrial Research
# Organisation (CSIRO) ABN 41 687 119 230.
#
# All rights reserved. CSIRO is willing to grant you a licence to the eChronos
# real-time operating system under the terms of the CSIRO_BSD_MIT license. See
# the file "LICENSE_CSIRO_BSD_MIT.txt" for details.
#
# @TAG(CSIRO_BSD_MIT)
#

from collections import namedtuple
import difflib
import os
import shutil
import subprocess
from .utils import Git, string_to_path, walk, LineFilter, update_file, get_release_version


TaskConfiguration = namedtuple('TaskConfiguration', ('repo_path', 'tasks_path', 'description_template_path',
                                                     'reviews_path', 'mainline_branch', 'manage_release_version'))


class Task:
    """Represents a development task.

    Each task is associated with several task-related resources, such as the corresponding git branch, a description
    file, and reviews.
    Over its life time, a task traverses several states (such as ready for implementation, complete and ready for
    integration, and integrated).
    This class implements some aspects of task management and helps automating state transitions.
    """

    def __init__(self, cfg, name=None, checkout=True):
        """Instantiate a task object based on given configuration.

        The task lives in the repo_path directory.
        This means that repo_path is a local git repository and that all task-related files are managed inside it.

        If `name` is None, it defaults to the name of active git branch in repo_path.

        If `name` contains unsupported characters, this function raises an _InvalidTaskNameError exception.

        `name` does not necessarily need to identify an existing task or git branch.
        In that case, the task object at first only supports the `create()` function to create the task proper.

        `checkout` controls whether this function checks out the task git branch to make it the active branch.
        """
        self.cfg = cfg
        self._git = Git(self.cfg.repo_path)

        if name is None:
            self.name = self._git.get_active_branch()
        else:
            if not Task._is_valid_name(name):
                raise _InvalidTaskNameError('The task name "{}" contains unsupported characters. '
                                            'Only letters, digits, dashes, and underscores are supported.'
                                            .format(name))
            self.name = name
            if checkout:
                self._git.checkout(self.name)

        self._review_dir = os.path.join(self.cfg.reviews_path, self.name)
        self._review_placeholder_path = os.path.join(self._review_dir,
                                                     '.placeholder_for_git_to_not_remove_this_otherwise_empty_dir')
        self._mainline_tracking_branch = self._git.get_tracking_branch(self.cfg.mainline_branch)

    def create(self, offline=False):
        self._check_and_prepare(check_active=False, update=False, check_mainline=False, offline=offline)
        if not offline:
            self._git.fetch()

        if self.name in self._git.branches:
            raise _InvalidTaskNameError('The task name "{}" is not unique as the git branch "{}" already exists.'
                                        .format(self.name, self.name))

        self._git.branch(self.name, self._mainline_tracking_branch, track=False)
        self._git.checkout(self.name)
        if not offline:
            self._git.push(self.name, set_upstream=True)

        shutil.copyfile(self.cfg.description_template_path, self._description_path)
        self._git.add([self._description_path])

        print('1. edit file "{}"\n'
              '2. commit via #> git commit -m "New task: {}" {}\n'
              '3. push task to remote repository via #> git push'.format(self._description_path, self.name,
                                                                         self._description_path))

    def integrate(self, offline=False):
        self._check_and_prepare(offline=offline)
        if not self._is_on_review():
            raise _InvalidTaskStateError('The task {} is not on review.'.format(self.name))
        self._check_is_accepted()

        if self.cfg.manage_release_version:
            release_cfg_path = self._update_release_version(offline=offline)
        self._git.checkout(self.cfg.mainline_branch)
        self._git.merge_into_active_branch(self._mainline_tracking_branch, '--ff-only', '--no-squash')
        self._git.merge_into_active_branch(self.name, '--no-squash')
        if self.cfg.manage_release_version:
            tag_name = 'v' + '.'.join(str(part) for part in get_release_version(release_cfg_path))
            self._git.tag(tag_name, 'master')
        if not offline:
            self._git.push()
            if self.cfg.manage_release_version:
                self._git.push(tag_name)

    def _check_is_accepted(self):
        """Check whether all authors of completed reviews arrive at the 'accepted' conclusion in their final reviews,
        and that at least two review authors have done so.
        """
        reviews = self._get_most_recent_reviews()
        if not reviews:
            raise _InvalidTaskStateError('Task {} has not been reviewed'.format(self.name))
        for review in reviews:
            if not review.is_accepted():
                raise _InvalidTaskStateError('The conclusion of review {} for task {} is not "accepted"'.
                                             format(review.file_path, self.name))
        if len(reviews) < 2:
            raise _InvalidTaskStateError('Task {} does not have enough reviews (minimum: 2)'.format(self.name))

    def _get_most_recent_reviews(self):
        """For any reviewer having reviewed this task, determine the most recent review and return all of them as a
        list of _Review instances.
        """
        reviews_by_author = {}
        for review in self._get_reviews():
            if review.author in reviews_by_author:
                if reviews_by_author[review.author].round < review.round:
                    reviews_by_author[review.author] = review
            else:
                reviews_by_author[review.author] = review
        return reviews_by_author.values()

    def _get_reviews(self):
        """Retrieve and return a list of _Review instances that represents all reviews of this task, even uncompleted
        ones.
        """
        reviews = []
        directory_contents = os.listdir(self._review_dir)
        directory_contents.sort()
        for relative_path in directory_contents:
            absolute_path = os.path.join(self._review_dir, relative_path)
            if os.path.isfile(absolute_path) and not relative_path.startswith('.'):
                review = _Review(absolute_path)
                reviews.append(review)
        return reviews

    def request_reviews(self, offline=False):
        """Mark the current branch as up for review.

        - create the review directory
        - create the empty file .placeholder_for_git_to_not_remove_this_otherwise_empty_dir in the review direcotry
        - commit the result
        - push the commit to the remote
        """
        self._check_and_prepare(offline=offline)
        if self._is_on_review():
            raise _InvalidTaskStateError('The task {} is already on review.'.format(self.name))

        os.makedirs(self._review_dir, exist_ok=False)
        open(self._review_placeholder_path, 'w').close()

        self._git.add(files=[self._review_dir])
        self._git.commit('Review request for {}'.format(self.name), files=[self._review_dir])

        if not offline:
            self._git.push()

    def _update_release_version(self, offline=False):
        release_cfg_path = self._update_release_version_file()
        self._git.add(files=[release_cfg_path])
        self._git.commit('{}\nUpdate {} number of release version.'.format(self.name, self._get_release_impact()),
                         files=[release_cfg_path])
        if not offline:
            self._git.push()
        return release_cfg_path

    def _update_release_version_file(self):
        prefix = '    version = '
        release_impact = self._get_release_impact()

        def matches(_, line, __, ___):
            return line.startswith(prefix)

        def replace(_, line, line_no, path):
            try:
                current_version_str = line.split(prefix)[1].strip().strip("'")
                major, minor, patch = (int(part) for part in current_version_str.split('.'))
            except (IndexError, ValueError):
                raise _InvalidVersionError('Unable to parse release version in line {} ("{}") of the release '
                                           'configuration file "{}"'.format(line_no, line, path))
            if release_impact == 'major':
                major += 1
                minor = 0
                patch = 0
            elif release_impact == 'minor':
                minor += 1
                patch = 0
            elif release_impact == 'patch':
                patch += 1
            return "{}'{}.{}.{}'\n".format(prefix, major, minor, patch)

        def handle_no_matches(_, path):
            raise _InvalidVersionError('Unable to find release version number based on prefix "{}" in release '
                                       'configuration file "{}"'.format(prefix, path))

        release_cfg_path = os.path.join(self.cfg.repo_path, 'release_cfg.py')
        version_line_filter = LineFilter(matches, replace, handle_no_matches)
        update_file(release_cfg_path, (version_line_filter,), only_if_all_matched=True)

        return release_cfg_path

    def review(self, offline=False, accept=False):
        self._check_and_prepare(offline=offline)
        if not self._is_on_review():
            raise _InvalidTaskStateError('The task {} is not on review.'.format(self.name))

        reviewer = self._git.get_user_name()
        reviewer_name_as_path = self._get_reviewer_name_as_path(reviewer)
        review_path_template = os.path.join(self._review_dir, '{}.{{}}.md'.format(reviewer_name_as_path))
        for review_round in range(1000):
            review_path = review_path_template.format(review_round)
            if not os.path.exists(review_path):
                break
        else:
            raise FileNotFoundError('Unable to determine review round for task "{}" and reviewer "{}" ("{}")'
                                    .format(self.name, reviewer, review_path_template))

        if not accept:
            review_template = """Reviewer: {} ({})
Conclusion: Accepted/Rework

Location: filename:linenum
Comment:
"""
        else:
            review_template = """Reviewer: {} ({})
Conclusion: Accepted
"""
        review_contents = review_template.format(reviewer, self._git.get_user_email())
        open(review_path, 'wb').write(review_contents.encode('UTF-8'))
        files_to_commit = []
        self._git.add([review_path])
        files_to_commit.append(review_path)
        if os.path.exists(self._review_placeholder_path):
            self._git.rm([self._review_placeholder_path])
            files_to_commit.append(self._review_placeholder_path)

        if not accept:
            print('To complete the review, edit the file "{}" and commit and push it with the commands\n\
    git commit {}\n\
    git push'.format(review_path, ' '.join(files_to_commit)))
        else:
            self._git.commit('Review task {}: accepted, 0 comments'.format(self.name))
            if not offline:
                self._git.push()

    def _get_reviewer_name_as_path(self, name):
        name_as_path = string_to_path(name)
        other_names_as_paths = self._get_reviewer_names_from_paths()
        if name_as_path not in other_names_as_paths:
            close_matches = difflib.get_close_matches(name_as_path, other_names_as_paths)
            if close_matches:
                answer = input('Your review goes into a file like "{}.*.md". \
There already are reviews with very similar prefixes:\n\
    {}.\n\
Might you have used any of those in the past? (Y/n)'.format(name_as_path, close_matches))
                if not answer or answer.lower() == 'y':
                    raise _InconsistentUserNameError('\
It seems that you wrote previous reviews under a different git user name. \
To keep things consistent, please use "git config --global user.name" to update your git user name. \
Your git user name should be consistent across all your repositories and match that of previous reviews. \
This is necessary for our review system to work as expected.')

        return name_as_path

    def _get_reviewer_names_from_paths(self):
        # collect all reviews in the repo
        review_paths = walk(self.cfg.reviews_path, lambda p: not p.endswith('.md'))
        # rsplit() helps to account for user names containing '.'
        reviewer_names = [os.path.basename(p).rsplit('.', 2)[0] for p in review_paths]
        return frozenset(reviewer_names)

    def update(self, offline=False):
        self._check_and_prepare(offline=offline, check_mainline=False)

        if self._is_on_review():
            self._git.merge_into_active_branch(self._mainline_tracking_branch, '--no-squash')
            self._git.push(force=False)
        else:
            self._git.rebase(self._mainline_tracking_branch)
            self._git.push(force=True)

    def _check_and_prepare(self, check_active=True, update=True, check_mainline=True, offline=False):
        if check_active:
            active_branch = self._git.get_active_branch()
            if active_branch != self.name:
                raise _InvalidTaskStateError('Task {} is not the active checked-out branch ({}) in repository {}'.
                                             format(self.name, active_branch, self.cfg.repo_path))

        if not self._git.is_clean():
            raise _InvalidTaskStateError('The local git repository contains staged or unstaged changes.')

        if update and not self._git.is_ref_uptodate_with_tracking_branch(offline=offline):
            try:
                self._git.merge_into_active_branch(self._git.get_tracking_branch(), '--ff-only')
            except subprocess.CalledProcessError:
                raise _InvalidTaskStateError('The task branch is not up-to-date with its remote tracking branch.')

        if check_mainline and \
                self.name not in self._git.get_branches_that_contain_revid(self._mainline_tracking_branch):
            self.update(offline=offline)

    def _is_on_review(self):
        if self._git.get_active_branch() != self.name:
            raise _TaskNotActiveBranchError('The task {} is not the active git branch (the active git branch is {})'
                                            .format(self.name, self._git.get_active_branch()))
        return os.path.exists(self._review_dir)

    @staticmethod
    def _is_valid_name(name):
        return all([c.isalnum() or c in ('-', '_') for c in name])

    def _get_release_impact(self):
        """Return the release impact of the current task as documented in the task's description.

        This function either returns one of 'major', 'minor', or 'patch' or it raises an _InvalidReleaseImpactError.
        """
        prefix = '# Release Impact:'
        valid_values = frozenset(('major', 'minor', 'patch'))
        with open(self._description_path) as file_obj:
            for line_no, line in enumerate(file_obj, 1):
                if line.startswith(prefix):
                    try:
                        release_impact = line.split(prefix)[1].strip().lower()
                    except IndexError:
                        raise _InvalidReleaseImpactError('Unable to parse level of release impact from line {} ("{}")'
                                                         ' in task description file "{}"'
                                                         .format(line_no, line, self._description_path))
                    if release_impact not in valid_values:
                        raise _InvalidReleaseImpactError('The release impact value "{}" on line {} ("{}") in task '
                                                         'description file "{}" is not among the acceptable values '
                                                         '"{}"'.format(release_impact, line_no, line,
                                                                       self._description_path, valid_values))
                    return release_impact

        raise _InvalidReleaseImpactError('Unable to find section "{}" in task description file "{}"'
                                         .format(prefix, self._description_path))

    @property
    def _description_path(self):
        return os.path.join(self.cfg.repo_path, self.cfg.tasks_path, self.name)


class _Review:
    def __init__(self, file_path):
        """Create a _Review instance representing the review in the given 'file_path'.

        This provides easy access to the review's review round, author, and conclusion.
        """
        assert isinstance(file_path, str)
        assert os.path.isfile(file_path)
        self.file_path = file_path
        basename = os.path.basename(file_path)
        author_dot_round = os.path.splitext(basename)[0]
        author, round_ = author_dot_round.rsplit('.', maxsplit=1)
        self.round = int(round_)
        self.author = author
        self._conclusion = None

    def _get_conclusion(self):
        """Determine the conclusion of this review.

        The conclusion can be expected to be one of 'accepted/rework' (i.e., the review has not been completed),
        'accepted', or 'rework'.
        """
        file_obj = open(self.file_path)
        for line in file_obj:
            if line.startswith('Conclusion: '):
                conclusion = line.split(':')[1].strip()
                file_obj.close()
                return conclusion.lower()
        file_obj.close()
        assert False
        return False

    @property
    def conclusion(self):
        if self._conclusion is None:
            self._conclusion = self._get_conclusion()
        return self._conclusion

    def is_accepted(self):
        return self.conclusion in ('accept', 'accepted')


class _TaskNotActiveBranchError(RuntimeError):
    """Indicates that a Task object does not represent the currently active branch in the local git repository."""
    pass


class _InvalidTaskStateError(RuntimeError):
    """Indicates that a task state transition cannot occur because the task is not in the appropriate source state.
    """
    pass


class _InvalidTaskNameError(RuntimeError):
    pass


class _InconsistentUserNameError(RuntimeError):
    pass


class _InvalidReleaseImpactError(Exception):
    pass


class _InvalidVersionError(Exception):
    pass
