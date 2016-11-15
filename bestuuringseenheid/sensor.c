#include <avr/io.h>
#include <avr/interrupt.h>

void init_adc(){
	//Input pin = A0 (PC0)
	ADMUX = (1<<REFS0);
	//Enable ADC & Prescaler = 128 & Enable ADC interrupts
	ADCSRA = (1<<ADEN)|(1<<ADPS2)|(1<<ADPS1)|(1<<ADPS0)|(1<<ADIE)|(1<<ADIF);
}

enum sensor_types {
	LIGHT = 1,
	TEMP = 2
};

enum sensor_types sensor_type = 
#ifdef light
LIGHT
#endif
#ifdef temp
TEMP
#endif
;

unsigned int sensor_data = 0;

uint64_t sensor_sum = 0;
uint16_t sensor_count = 0;

void update_data() {
	sensor_data = sensor_sum / sensor_count;
	#ifdef light
		sensor_data /= 100;
	#endif
	#ifdef temp
		sensor_data /= 10;
	#endif
	sensor_count = 0;
	sensor_sum = 0;
}

ISR(ADC_vect){
	uint64_t miliVolts = (500000/1024*ADC)/100;

	#ifdef light
	uint64_t rldr;

	if (miliVolts > 1)
	{
		rldr = (100*(5000-miliVolts))/miliVolts;
	} else {
		rldr = 500000;
	}
	sensor_sum += 50000/rldr;
	#endif
	#ifdef temp
	sensor_sum += miliVolts;
	#endif

	sensor_count++;
}

// Echo on D3
// Trig on D2

void init_distance() {
	EICRA |= (1 << ISC10);
	EIMSK |= (1 << INT1);
	TCCR0A = 0;
	TCCR0B = (1 << CS01) | (1 << CS00);
	TIMSK0 = (1 << TOIE0);
	DDRD |= (1 << 2);
}

unsigned int time = 0;
unsigned int distance = 0;

ISR (TIMER0_OVF_vect) {
	time+= 1<<8;
}

ISR (INT1_vect) {
	if (PIND & (1 << 3)) {
		TCNT0 = 0;
		time = 0;
	} else {
		time += TCNT0;
		distance = time * (64 / 16) / 58;
	}
}

void sensor_start() {
	ADCSRA |= (1<<ADSC);
	PORTD |= (1 << 2);
	_delay_ms(1);
	PORTD &= ~(1 << 2);
}

void sensor_init() {
	init_adc();
	init_distance();
}
