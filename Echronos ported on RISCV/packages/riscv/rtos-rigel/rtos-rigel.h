#ifndef RTOS_RIGEL_H
#define RTOS_RIGEL_H
#include <stdint.h>

#include <stdint.h>

typedef uint8_t {{prefix_type}}ErrorId;

typedef uint{{taskid_size}}_t {{prefix_type}}TaskId;







#define {{prefix_const}}TASK_ID_ZERO (({{prefix_type}}TaskId) UINT{{taskid_size}}_C(0))
#define {{prefix_const}}TASK_ID_MAX (({{prefix_type}}TaskId)UINT{{taskid_size}}_C({{tasks.length}} - 1))
{{#tasks}}
#define {{prefix_const}}TASK_ID_{{name|u}} (({{prefix_type}}TaskId) UINT{{taskid_size}}_C({{idx}}))
{{/tasks}}









#ifdef __cplusplus
extern "C" {
#endif


/*@unused@*/
{{prefix_type}}TaskId {{prefix_func}}task_current(void);
/*@unused@*/
void {{prefix_func}}yield(void) {{prefix_const}}REENTRANT;
/*@unused@*/
void {{prefix_func}}task_start({{prefix_type}}TaskId task);



void {{prefix_func}}start(void);
#ifdef __cplusplus
}
#endif

#endif /* RTOS_RIGEL_H */