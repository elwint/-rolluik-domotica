// UP is B0
// ACTIVE is B1
// DOWN is B2

void led_update() {
	if (state == STATE_UP) {
		PORTB |= 1;
		PORTB &= ~(1<<2);
	} else {
		PORTB |= (1<<2);
		PORTB &= ~1;
	}

	if (!done) {
		PORTB ^= (1<<1);
	} else {
		PORTB &= ~(1<<1);
	}
}

void led_init() {
	DDRB |= 0b00000111;
	PORTB &= ~0b00000111;
	led_update();
}
