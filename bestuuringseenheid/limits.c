unsigned int min_distance =   5;
unsigned int max_distance = 160;
unsigned int margin_distance = 5;

#ifdef light
unsigned int margin_sensor = 2;
unsigned int up_sensor = 40;
unsigned int down_sensor = 70;
#endif
#ifdef temp
unsigned int margin_sensor = 3;
unsigned int up_sensor = 15;
unsigned int down_sensor = 20;
#endif

uint8_t done = 1;

enum state_t {
	STATE_NONE = 0,
	STATE_UP = 1,
	STATE_DOWN = 2
};

enum state_t state = STATE_NONE;

uint8_t forced = 0;

void state_update() {
	if (forced) {
		return;
	}
	enum state_t newstate = STATE_NONE;
	if ((sensor_data - margin_sensor) <= up_sensor) {
		newstate = STATE_UP;
	}
	if ((sensor_data + margin_sensor) >= down_sensor) {
		newstate = STATE_DOWN;
	}

	if ((newstate != STATE_NONE) && (newstate != state)) {
		state = newstate;
		done = 0;
		return;
	}

	if (state == STATE_NONE) {
		state = STATE_UP;
		done = 0;
		return;
	}

	int target = 0;

	if (state == STATE_UP) {
		target = min_distance;
	} else {
		target = max_distance;
	}

	if ((distance >= (target-margin_distance)) && (distance <= (target+margin_distance))) {
		done = 1;
	}

}

void state_init() {
	if ((distance - margin_distance) <= min_distance) {
		state = STATE_UP;
	} else if ((distance + margin_distance) >= max_distance) {
		state = STATE_DOWN;
	}
}
