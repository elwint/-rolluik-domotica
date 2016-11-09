#include "protocol.c"
#include "AVR_TTC_scheduler.c"

void count();

int main() {
	protocol_init();

	SCH_Init_T1();

	SCH_Add_Task(protocol_handler, 0, 1);

	SCH_Start();

	while(1) {
		SCH_Dispatch_Tasks();
	}
	
	return 0;
}
