#include <stdint.h>

#include <stdint.h>
#include "rtos-rigel.h"
#define ERROR_ID_NONE (({{prefix_type}}ErrorId) UINT8_C(0))
#define ERROR_ID_TICK_OVERFLOW (({{prefix_type}}ErrorId) UINT8_C(1))
#define ERROR_ID_INVALID_ID (({{prefix_type}}ErrorId) UINT8_C(2))
#define ERROR_ID_NOT_HOLDING_MUTEX (({{prefix_type}}ErrorId) UINT8_C(3))
#define ERROR_ID_DEADLOCK (({{prefix_type}}ErrorId) UINT8_C(4))
#define ERROR_ID_TASK_FUNCTION_RETURNS (({{prefix_type}}ErrorId) UINT8_C(5))
#define ERROR_ID_INTERNAL_CURRENT_TASK_INVALID (({{prefix_type}}ErrorId) UINT8_C(6))
#define ERROR_ID_INTERNAL_INVALID_ID (({{prefix_type}}ErrorId) UINT8_C(7))
#define ERROR_ID_MESSAGE_QUEUE_BUFFER_OVERLAP (({{prefix_type}}ErrorId) UINT8_C(8))
#define ERROR_ID_MESSAGE_QUEUE_ZERO_TIMEOUT (({{prefix_type}}ErrorId) UINT8_C(9))
#define ERROR_ID_MESSAGE_QUEUE_INTERNAL_ZERO_TIMEOUT (({{prefix_type}}ErrorId) UINT8_C(10))
#define ERROR_ID_MESSAGE_QUEUE_INVALID_POINTER (({{prefix_type}}ErrorId) UINT8_C(11))
#define ERROR_ID_MESSAGE_QUEUE_INTERNAL_TICK_OVERFLOW (({{prefix_type}}ErrorId) UINT8_C(12))
#define ERROR_ID_MESSAGE_QUEUE_INTERNAL_INCORRECT_INITIALIZATION (({{prefix_type}}ErrorId) UINT8_C(13))
#define ERROR_ID_MESSAGE_QUEUE_INTERNAL_VIOLATED_INVARIANT_CONFIGURATION (({{prefix_type}}ErrorId) UINT8_C(14))
#define ERROR_ID_MESSAGE_QUEUE_INTERNAL_VIOLATED_INVARIANT_INVALID_HEAD (({{prefix_type}}ErrorId) UINT8_C(15))
#define ERROR_ID_MESSAGE_QUEUE_INTERNAL_VIOLATED_INVARIANT_INVALID_AVAILABLE (({{prefix_type}}ErrorId) UINT8_C(16))
#define ERROR_ID_MESSAGE_QUEUE_INTERNAL_VIOLATED_INVARIANT_INVALID_ID_IN_WAITERS (({{prefix_type}}ErrorId) UINT8_C(17))
#define ERROR_ID_MESSAGE_QUEUE_INTERNAL_VIOLATED_INVARIANT_TASKS_BLOCKED_DESPITE_AVAILABLE_MESSAGES (({{prefix_type}}ErrorId) UINT8_C(18))
#define ERROR_ID_MESSAGE_QUEUE_INTERNAL_VIOLATED_INVARIANT_WAITING_TASK_IS_NOT_BLOCKED (({{prefix_type}}ErrorId) UINT8_C(19))
#define ERROR_ID_MESSAGE_QUEUE_INTERNAL_VIOLATED_INVARIANT_INVALID_MESSAGES_POINTER (({{prefix_type}}ErrorId) UINT8_C(20))
#define ERROR_ID_MESSAGE_QUEUE_INTERNAL_VIOLATED_INVARIANT_INVALID_MESSAGE_SIZE (({{prefix_type}}ErrorId) UINT8_C(21))
#define ERROR_ID_MESSAGE_QUEUE_INTERNAL_VIOLATED_INVARIANT_INVALID_QUEUE_LENGTH (({{prefix_type}}ErrorId) UINT8_C(22))
#define ERROR_ID_INTERNAL_PRECONDITION_VIOLATED (({{prefix_type}}ErrorId) UINT8_C(23))
#define ERROR_ID_INTERNAL_POSTCONDITION_VIOLATED (({{prefix_type}}ErrorId) UINT8_C(24))
#define ERROR_ID_SEMAPHORE_MAX_INVALID (({{prefix_type}}ErrorId) UINT8_C(25))
#define ERROR_ID_SEMAPHORE_MAX_USE_BEFORE_INIT (({{prefix_type}}ErrorId) UINT8_C(26))
#define ERROR_ID_SEMAPHORE_MAX_ALREADY_INIT (({{prefix_type}}ErrorId) UINT8_C(27))
#define ERROR_ID_SEMAPHORE_MAX_EXCEEDED (({{prefix_type}}ErrorId) UINT8_C(28))
#define ERROR_ID_MESSAGE_QUEUE_INTERNAL_VIOLATED_INVARIANT_TIMER_IS_ENABLED (({{prefix_type}}ErrorId) UINT8_C(29))
#define ERROR_ID_SCHED_PRIO_CEILING_TASK_LOCKING_LOWER_PRIORITY_MUTEX (({{prefix_type}}ErrorId) UINT8_C(30))
#define ERROR_ID_SCHED_PRIO_CEILING_MUTEX_ALREADY_LOCKED (({{prefix_type}}ErrorId) UINT8_C(31))
#define ERROR_ID_TIMER_SIGNAL_SET_IS_EMPTY (({{prefix_type}}ErrorId) UINT8_C(32))
#define ERROR_ID_MPU_INTERNAL_MISALIGNED_ADDR (({{prefix_type}}ErrorId) UINT8_C(33))
#define ERROR_ID_MPU_INTERNAL_INVALID_PTR (({{prefix_type}}ErrorId) UINT8_C(34))
#define ERROR_ID_MPU_VIOLATION (({{prefix_type}}ErrorId) UINT8_C(35))
#define ERROR_ID_MPU_ALREADY_ENABLED (({{prefix_type}}ErrorId) UINT8_C(36))
#define ERROR_ID_MPU_ALREADY_DISABLED (({{prefix_type}}ErrorId) UINT8_C(37))
#define ERROR_ID_MPU_INVALID_REGION_SIZE (({{prefix_type}}ErrorId) UINT8_C(38))
#define ERROR_ID_MPU_NON_STANDARD (({{prefix_type}}ErrorId) UINT8_C(39))
#define ERROR_ID_MPU_SANITATION_FAILURE (({{prefix_type}}ErrorId) UINT8_C(40))
#define ERROR_ID_MPU_INTERNAL_INVALID_REGION_INDEX (({{prefix_type}}ErrorId) UINT8_C(41))

/* The TASK_ID_NONE and TASK_ID_END macros require some care:
 * - TASK_ID_NONE is a valid integer within the value range of the TaskIdOption/TaskId types.
 *   There is no fundamental safeguard against the application defining TASK_ID_NONE+1 tasks so that the last task
 *   receives a task ID that is numerically equal to TASK_ID_NONE.
 * - TASK_ID_END is of type integer, not TaskIdOption/TaskId.
 *   It may hold the value TASK_ID_MAX + 1 which potentially exceeds the valid value range of TaskIdOption/TaskId.
 *   It can therefore not necessarily be safely assigned to or cast to type TaskIdOption/TaskId. */
#define TASK_ID_NONE ((TaskIdOption) UINT{{taskid_size}}_MAX)
#define TASK_ID_END ({{tasks.length}})
#define current_task rtos_internal_current_task
#define tasks rtos_internal_tasks

typedef {{prefix_type}}TaskId TaskIdOption;


struct task
{
    context_t ctx;
};

extern /*@noreturn@*/ void {{fatal_error}}({{prefix_type}}ErrorId error_id);
{{#mpu_enabled}}
extern void rtos_internal_elevate_privileges(void);
extern void rtos_internal_drop_privileges(void);
extern uint32_t rtos_internal_in_usermode(void);
{{/mpu_enabled}}
{{#tasks}}
extern void {{function}}(void);
{{/tasks}}
{{#profiling}}
{{#profiling.hook_for_task_switch}}
extern void {{hook_for_task_switch}}({{prefix_type}}TaskId from, {{prefix_type}}TaskId to);
{{/profiling.hook_for_task_switch}}
{{/profiling}}


{{#internal_asserts}}
static {{prefix_type}}TaskId get_current_task_check(void);
{{/internal_asserts}}
static void yield_to({{prefix_type}}TaskId to) {{prefix_const}}REENTRANT;
static void block(void) {{prefix_const}}REENTRANT;
static void unblock({{prefix_type}}TaskId task);

{{#mpu_enabled}}
uint32_t rtos_internal_api_depth[{{tasks.length}}] = {0};
{{/mpu_enabled}}
/*@unused@ must be public so that packages/armv7m/ctxt-switch-preempt.s can access this symbol */
{{prefix_type}}TaskId rtos_internal_current_task;
/*@unused@ must be public so that packages/armv7m/ctxt-switch-preempt.s can access this symbol */
struct task rtos_internal_tasks[{{tasks.length}}];
static {{prefix_type}}TimerId task_timers[{{tasks.length}}] = {
{{#tasks}}
    {{prefix_const}}TIMER_ID_{{timer.name|u}},
{{/tasks}}
};
{{#api_asserts}}
#define api_error(error_id) {{fatal_error}}(error_id)
{{/api_asserts}}
{{^api_asserts}}
#define api_error(error_id)
{{/api_asserts}}
{{#api_asserts}}
#define api_assert(expression, error_id) do { if (!(expression)) { api_error(error_id); } } while(0)
{{/api_asserts}}
{{^api_asserts}}
#define api_assert(expression, error_id)
{{/api_asserts}}

{{#internal_asserts}}
#define internal_error(error_id) {{fatal_error}}(error_id)
{{/internal_asserts}}
{{^internal_asserts}}
#define internal_error(error_id)
{{/internal_asserts}}
{{#internal_asserts}}
#define internal_assert(expression, error_id) do { if (!(expression)) { internal_error(error_id); } } while(0)
{{/internal_asserts}}
{{^internal_asserts}}
#define internal_assert(expression, error_id)
{{/internal_asserts}}
{{^mpu_enabled}}
#define rtos_internal_api_begin()
#define rtos_internal_api_end()
{{/mpu_enabled}}

{{#mpu_enabled}}
#define rtos_internal_api_begin() \
    if(rtos_internal_in_usermode()) { \
        rtos_internal_elevate_privileges(); \
    } \
    ++rtos_internal_api_depth[rtos_internal_current_task];

#define rtos_internal_api_end() \
    if(--rtos_internal_api_depth[rtos_internal_current_task] == 0) { \
        rtos_internal_drop_privileges(); \
    }
{{/mpu_enabled}}
{{#internal_asserts}}
#define get_current_task() get_current_task_check()
{{/internal_asserts}}
{{^internal_asserts}}
#define get_current_task() current_task
{{/internal_asserts}}
#define get_task_context(task_id) &tasks[task_id].ctx
#define internal_assert_task_valid(task) internal_assert(task < {{tasks.length}}, ERROR_ID_INTERNAL_INVALID_ID)
#define assert_task_valid(task) api_assert(task < {{tasks.length}}, ERROR_ID_INVALID_ID)
#define yield() {{prefix_func}}yield()
#define interrupt_event_id_to_taskid(interrupt_event_id) (({{prefix_type}}TaskId)(interrupt_event_id))
#define mutex_core_block_on(unused_task) {{prefix_func}}signal_wait({{prefix_const}}SIGNAL_ID__TASK_TIMER)
#define mutex_core_unblock(task) {{prefix_func}}signal_send(task, {{prefix_const}}SIGNAL_ID__TASK_TIMER)
#define message_queue_core_block() {{prefix_func}}signal_wait({{prefix_const}}SIGNAL_ID__TASK_TIMER)
/* sleep() may return before the timeout occurs because another task may send the timeout signal to indicate that the
 * state of the message queue has changed.
 * Therefore, disable the timer whenever sleep() returns to make sure the timer is no longer active.
 * Note that in the current message-queue implementation, this is not necessary for correctness.
 * The message-queue implementation handles spurious timer signals gracefully.
 * However, disabling the timer avoids confusion and provides a minor benefit in run-time efficiency. */
#define message_queue_core_block_timeout(timeout)\
do\
{\
    {{prefix_func}}sleep((timeout));\
    {{prefix_func}}timer_disable(task_timers[get_current_task()]);\
}\
while (0)
#define message_queue_core_unblock(task) {{prefix_func}}signal_send((task), {{prefix_const}}SIGNAL_ID__TASK_TIMER)
#define message_queue_core_is_unblocked(task) sched_runnable((task))


{{#internal_asserts}}
static {{prefix_type}}TaskId
get_current_task_check(void)
{
    internal_assert(current_task < {{tasks.length}}, ERROR_ID_INTERNAL_CURRENT_TASK_INVALID);
    return current_task;
}
{{/internal_asserts}}
static void
yield_to(const {{prefix_type}}TaskId to) {{prefix_const}}REENTRANT
{
    const {{prefix_type}}TaskId from = get_current_task();

    internal_assert(to < {{tasks.length}}, ERROR_ID_INTERNAL_INVALID_ID);

    {{#profiling}}
    {{#profiling.hook_for_task_switch}}
    {{hook_for_task_switch}}(from, to);
    {{/profiling.hook_for_task_switch}}
    {{/profiling}}

    current_task = to;
    context_switch(get_task_context(from), get_task_context(to));
}

static void
block(void) {{prefix_const}}REENTRANT
{
    sched_set_blocked(get_current_task());
    {{prefix_func}}yield();
}

static void
unblock(const {{prefix_type}}TaskId task)
{
    sched_set_runnable(task);
}

/* entry point trampolines */
{{#tasks}}
static void
entry_{{name}}(void)
{
    {{#start}}{{prefix_func}}yield();{{/start}}
    {{^start}}{{prefix_func}}signal_wait({{prefix_const}}SIGNAL_ID__RTOS_UTIL);{{/start}}
    {{function}}();

    api_error(ERROR_ID_TASK_FUNCTION_RETURNS);
}

{{/tasks}}


{{prefix_type}}TaskId
{{prefix_func}}task_current(void)
{
    {{prefix_type}}TaskId t;
    rtos_internal_api_begin();
    t = get_current_task();
    rtos_internal_api_end();
    return t;
}
void
{{prefix_func}}task_start(const {{prefix_type}}TaskId task)
{
    assert_task_valid(task);
    {{prefix_func}}signal_send(task, {{prefix_const}}SIGNAL_ID__RTOS_UTIL);
}

void
{{prefix_func}}yield(void) {{prefix_const}}REENTRANT
{
    {{prefix_type}}TaskId to = interrupt_event_get_next();
    yield_to(to);
}



void
{{prefix_func}}start(void)
{
    message_queue_init();

    {{#tasks}}
    context_init(get_task_context({{idx}}), entry_{{name}}, stack_{{idx}}, {{stack_size}});
    sched_set_runnable({{idx}});
    {{/tasks}}

    context_switch_first(get_task_context({{prefix_const}}TASK_ID_ZERO));
}
