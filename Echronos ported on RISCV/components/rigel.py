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

import os.path
from prj import SystemParseError, Module


class RigelModule(Module):
    xml_schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.xml')
    files = [
        {'input': 'rtos-rigel.h', 'render': True},
        {'input': 'rtos-rigel.c', 'render': True, 'type': 'c'},
    ]

    def configure(self, xml_config):
        config = super().configure(xml_config)

        # This variant does not support memory protection at this time
        config['mpu_enabled'] = False

        config['prefix_func'] = config['prefix'] + '_' if config['prefix'] is not None else ''
        config['prefix_type'] = config['prefix'].capitalize() if config['prefix'] is not None else ''
        config['prefix_const'] = config['prefix'].upper() + '_' if config['prefix'] is not None else ''

        # Ensure that at least one task is runnable.
        if not any(task['start'] for task in config['tasks']):
            raise SystemParseError("At least one task must be configured to start.")

        # Semi-configurable items
        # These are configurable in the code, but for simplicitly they are not supported as
        # user configuration at this stage.
        config['interrupteventid_size'] = 8
        config['taskid_size'] = 8

        # Create builtin signals
        # The RTOS task timer signal is used in the following conditions:
        #   1. To notify the task when a mutex is unlocked.
        #   2. To notify the task when a message queue has available messages / space
        # The same signal is re-used to avoid excessive allocation of signals.
        # This is safe as a task can not be simultaneously waiting for a mutex, and waiting on a message queue.
        config['signal_labels'].append({'name': '_task_timer', 'global': True})

        # The RTOS utility signal is used to start the task.
        config['signal_labels'].append({'name': '_rtos_util', 'global': True})

        # Assign signal ids
        sig_sets = []
        for task in config['tasks']:
            sig_set = []
            for sig in config['signal_labels']:
                if sig.get('global', False) or task['name'] in [t['name'] for t in sig['tasks']]:
                    sig_set.append(sig['name'])
            sig_sets.append(sig_set)

        label_ids = assign_signal_vals(sig_sets)
        for sig in config['signal_labels']:
            sig['idx'] = label_ids[sig['name']]

        # Create signal_set definitions from signal definitions:
        config['signal_sets'] = [{'name': sig['name'], 'value': 1 << sig['idx'], 'singleton': True}
                                 for sig in config['signal_labels']]

        signal_set_names = [sigset['name'] for sigset in config['signal_sets']]

        for interrupt_event in config['interrupt_events']:
            if interrupt_event['sig_set'] not in signal_set_names:
                msg = "Unknown signal-set '{}' in interrupt_event '{}'"
                raise SystemParseError(msg.format(interrupt_event['sig_set'], interrupt_event['name']))

        for timer in config['timers']:
            if timer['sig_set'] is not None and timer['sig_set'] not in signal_set_names:
                msg = "Unknown signal-set '{}' in timer '{}'"
                raise SystemParseError(msg.format(timer['sig_set'], timer['name']))

        # Create a timer for each task
        for task in config['tasks']:
            timer = {'name': '_task_' + task['name'],
                     'error': 0,
                     'reload': 0,
                     'task': task,
                     'idx': len(config['timers']),
                     'enabled': False,
                     'sig_set': '_task_timer'}
            task['timer'] = timer
            config['timers'].append(timer)
        return config


def assign_signal_vals(sig_sets):
    """Assign values to each signal in a list of signal sets.

    Values are assigned so that the values in each set are unique.

    A greedy algorithm is used to minimise the signal values used.

    A dictionary of signal values index by signal is returned.

    """
    signals = set().union(*sig_sets)
    possible_vals = set(range(len(signals)))

    assigned = {}
    # Sort the signals so that assign_signal_vals is deterministic based on input.
    # Without sorting Python iterates the signals set in arbitrary order.
    # Note that possibly changes on each Python invocation based on the hashing seed.
    for sig in sorted(signals):
        used_vals = [{assigned.get(ss) for ss in sig_set} for sig_set in sig_sets if sig in sig_set]
        assigned[sig] = min(possible_vals.difference(*used_vals))

    assert all(len({assigned[x] for x in sig_set}) == len(sig_set) for sig_set in sig_sets)

    # Returned dictionary should only be used for lookup, not iteration to ensure overall process is deterministic.
    return assigned


module = RigelModule()  # pylint: disable=invalid-name
