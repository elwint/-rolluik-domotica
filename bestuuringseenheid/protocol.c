#include "uart.c"

enum command_t {
	COMMAND_PING = 1,
	COMMAND_ECHO = 2,
	COMMAND_SENSOR = 3,
	COMMAND_STATUS = 4,
	COMMAND_GET_LIMITS = 5,
	COMMAND_SET_LIMITS = 6,
	COMMAND_FORCE = 7,
	COMMAND_AUTO = 8
};

enum status_t {
	STATUS_OK = 0,
	STATUS_UNKNOWN_COMMAND = 1,
	STATUS_MISSING_DATA = 2,
	STATUS_INVALID_LIMITS = 3
};

void protocol_init() {
	uart_init();
}

void protocol_handler() {
	if (!uart_has_data()) {
		return;
	}

	enum command_t command = uart_get_uint8();
	uint16_t data = 0;

	switch (command) {
		case COMMAND_PING:
			uart_put_uint8(STATUS_OK);

			break;
		case COMMAND_ECHO:
			if (!uart_has_data()) {
				uart_put_uint8(STATUS_MISSING_DATA);
				break;
			}
			data = uart_get_uint16();
			uart_put_uint8(STATUS_OK);
			uart_put_uint16(data);

			break;
		case COMMAND_SENSOR:
			uart_put_uint8(STATUS_OK);

			uart_put_uint16(distance);
			uart_put_uint16(sensor_type);
			uart_put_uint16(sensor_data);

			break;
		case COMMAND_STATUS:
			uart_put_uint8(STATUS_OK);

			uart_put_uint16(forced);
			uart_put_uint16(state);
			uart_put_uint16(done);

			break;
		case COMMAND_GET_LIMITS:
			uart_put_uint8(STATUS_OK);

			uart_put_uint16(min_distance);
			uart_put_uint16(max_distance);
			uart_put_uint16(up_sensor);
			uart_put_uint16(down_sensor);

			break;
		case COMMAND_SET_LIMITS:
			if (!uart_has_data()) {
				uart_put_uint8(STATUS_MISSING_DATA);
				break;
			}
			unsigned int min_dist = uart_get_uint16();

			if (!uart_has_data()) {
				uart_put_uint8(STATUS_MISSING_DATA);
				break;
			}
			unsigned int max_dist = uart_get_uint16();

			if (!uart_has_data()) {
				uart_put_uint8(STATUS_MISSING_DATA);
				break;
			}
			unsigned int u_sensor = uart_get_uint16();

			if (!uart_has_data()) {
				uart_put_uint8(STATUS_MISSING_DATA);
				break;
			}
			unsigned int d_sensor = uart_get_uint16();

			if (((min_dist < 2 || min_dist > 400) || (max_dist < 2 || max_dist > 400) || (max_dist - min_dist < (margin_distance*2))) &&
				((u_sensor < min_sensor || u_sensor > max_sensor) || (d_sensor < min_sensor || d_sensor > max_sensor) || (d_sensor - u_sensor < (margin_sensor*2)))) {
				uart_put_uint8(STATUS_INVALID_LIMITS);
				break;
			}
			min_distance = min_dist;
			max_distance = max_dist;
			up_sensor    = u_sensor;
			down_sensor  = d_sensor;

			done = 0;

			uart_put_uint8(STATUS_OK);

			break;
		case COMMAND_FORCE:
			if (!uart_has_data()) {
				uart_put_uint8(STATUS_MISSING_DATA);
				break;
			}
			state = uart_get_uint16();
			forced = 1;
			done = 0;

			uart_put_uint8(STATUS_OK);

			break;
		case COMMAND_AUTO:
			forced = 0;

			uart_put_uint8(STATUS_OK);

			break;
		default: // Unknown command
			uart_put_uint8(STATUS_UNKNOWN_COMMAND);
	}
}
