#define F_CPU 16000000UL
#define BAUD 19200

#include <util/delay.h>

#include "sensor.c"
#include "protocol.c"
#include "AVR_TTC_scheduler.c"

void count();

int main() {
	protocol_init();
	sensor_init();

	SCH_Init_T1();

	SCH_Add_Task(protocol_handler, 0, 1);
	SCH_Add_Task(sensor_start, 0, 10);

	SCH_Start();

	while(1) {
		SCH_Dispatch_Tasks();
	}
	
	return 0;
}
