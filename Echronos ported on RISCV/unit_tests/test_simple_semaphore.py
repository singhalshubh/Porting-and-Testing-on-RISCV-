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

import ctypes
import itertools
import os
import sys
import unittest

from pylib.utils import get_executable_extension, base_path

NUM_SEMAPHORES = 10
ALL_SEMAPHORES = list(range(NUM_SEMAPHORES))
SEM_ID_NONE = 255
SEM_VALUE_ZERO = 0

NUM_TASKS = 10
ALL_TASKS = list(range(NUM_TASKS))


class SemaphoreStruct(ctypes.Structure):
    _fields_ = [("value", ctypes.c_ubyte)]


class SemaphoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):  # pylint: disable=invalid-name
        result = os.system("{} {} build posix.unittest.simple-semaphore"
                           .format(sys.executable, base_path('prj', 'app', 'prj.py')))
        system = "out/posix/unittest/simple-semaphore/system" + get_executable_extension()
        assert result == 0
        cls.impl = ctypes.CDLL(system)
        cls.impl_sem = ctypes.POINTER(SemaphoreStruct).in_dll(cls.impl, 'pub_semaphores')
        cls.impl_waiters = ctypes.POINTER(ctypes.c_ubyte).in_dll(cls.impl, 'pub_waiters')
        cls.impl.rtos_sem_try_wait.res_type = ctypes.c_bool
        cls.unblock_func_ptr = None
        cls.block_func_ptr = None
        cls.get_current_task_ptr = None

    # pylint: disable=no-self-argument
    def show_state(cls):
        print("WAITERS: {}".format([cls.impl_waiters[i] for i in ALL_TASKS]))
        print("SEMVALUES: {}".format([cls.impl_sem[i].value for i in ALL_SEMAPHORES]))

    # pylint: disable=no-self-argument
    def set_unblock_func(cls, function):
        cls.unblock_func_ptr = ctypes.CFUNCTYPE(None, ctypes.c_ubyte)(function)
        cls.impl.pub_set_unblock_ptr(cls.unblock_func_ptr)

    # pylint: disable=no-self-argument
    def set_block_func(cls, function):
        cls.block_func_ptr = ctypes.CFUNCTYPE(None)(function)
        cls.impl.pub_set_block_ptr(cls.block_func_ptr)

    # pylint: disable=no-self-argument
    def set_get_current_task_func(cls, function):
        cls.get_current_task_ptr = ctypes.CFUNCTYPE(ctypes.c_ubyte)(function)
        cls.impl.pub_set_get_current_task_ptr(cls.get_current_task_ptr)


class testSimpleSemaphore(SemaphoreTest):  # pylint: disable=invalid-name
    # Semaphore tests (white-box)
    def test_count(self):
        self.impl.pub_sem_init()

        post_count = 256

        # Check all semaphore start at value zero.
        for sem_id in ALL_SEMAPHORES:
            assert self.impl_sem[sem_id].value == SEM_VALUE_ZERO

        for test_sem_id in ALL_SEMAPHORES:
            # Check that on posting the value is incremented (only
            # on the single semaphore).
            for i in range(1, post_count):
                self.impl.rtos_sem_post(test_sem_id)
                for sem_id in ALL_SEMAPHORES:
                    assert self.impl_sem[sem_id].value == (i if sem_id == test_sem_id else SEM_VALUE_ZERO)

            # Now check that wait correctly decrements
            for i in reversed(range(0, post_count - 1)):
                self.impl.rtos_sem_wait(test_sem_id)
                for sem_id in ALL_SEMAPHORES:
                    assert self.impl_sem[sem_id].value == (i if sem_id == test_sem_id else SEM_VALUE_ZERO)

    def test_block(self):
        self.impl.pub_sem_init()

        current_task_id = None
        current_sem_id = None

        def get_current_task():
            return current_task_id
        self.set_get_current_task_func(get_current_task)

        def block_func():
            for task_id in ALL_TASKS:
                assert self.impl_waiters[task_id] == current_sem_id if task_id == current_task_id else SEM_ID_NONE
            self.impl.rtos_sem_post(current_sem_id)
        self.set_block_func(block_func)

        for current_task_id in ALL_TASKS:
            for current_sem_id in ALL_SEMAPHORES:
                self.impl.rtos_sem_wait(current_sem_id)
                for task_id in ALL_TASKS:
                    assert self.impl_waiters[task_id] == SEM_ID_NONE

    def test_unblock_multiple(self):
        """Test that calling 'post' will unblock the correct set of waiters."""
        unblocked = []

        def unblock_func(task_id):
            nonlocal unblocked
            unblocked.append(task_id)

        for test_sem_id in ALL_SEMAPHORES:
            for waiters in itertools.product([True, False], repeat=NUM_TASKS):
                self.impl.pub_sem_init()
                self.set_unblock_func(unblock_func)
                for i, waiting in enumerate(waiters):
                    self.impl_waiters[i] = test_sem_id if waiting else SEM_ID_NONE
                unblocked = []
                self.impl.rtos_sem_post(test_sem_id)
                for task_id in ALL_TASKS:
                    assert self.impl_waiters[task_id] == SEM_ID_NONE
                    if waiters[task_id]:
                        assert task_id in unblocked
                    else:
                        assert task_id not in unblocked

    # Semaphore tests (black-box)
    def test_simple(self):
        """Simple test of semaphore functionality."""
        self.impl.pub_sem_init()

        # Try wait all the semaphores
        # all should fail
        for sem_id in ALL_SEMAPHORES:
            assert not self.impl.rtos_sem_try_wait(sem_id)

        # Post once to all semaphores
        for sem_id in ALL_SEMAPHORES:
            self.impl.rtos_sem_post(sem_id)

        # Now waiting on all semaphores should succeed
        for sem_id in ALL_SEMAPHORES:
            assert self.impl.rtos_sem_try_wait(sem_id)

        # Trying to wait again should fail on all.
        for sem_id in ALL_SEMAPHORES:
            assert not self.impl.rtos_sem_try_wait(sem_id)

    def test_block_unblock(self):
        # Check that block/unblock is called correctly.
        #
        # This code is a little bit icky. It would be nice if it could
        # be improved.
        #
        self.impl.pub_sem_init()

        task_id = 5
        expected_blocks = 20

        block_calls = 0
        unblocked = None

        def unblock_func(task_id):
            nonlocal unblocked
            unblocked = task_id
        self.set_unblock_func(unblock_func)

        def block_func():
            nonlocal block_calls
            block_calls += 1
            if block_calls == expected_blocks:
                self.impl.rtos_sem_post(0)
        self.set_block_func(block_func)

        def get_current_task():
            return task_id
        self.set_get_current_task_func(get_current_task)

        self.impl.rtos_sem_wait(0)

        assert block_calls == expected_blocks
        assert unblocked == task_id

    def test_counting(self):
        self.impl.pub_sem_init()

        assert self.impl.rtos_sem_try_wait(0) == 0

        for _ in range(200):
            self.impl.rtos_sem_post(0)

        for _ in range(200):
            assert self.impl.rtos_sem_try_wait(0) == 1

        assert self.impl.rtos_sem_try_wait(0) == 0
