#include "uart.c"

enum command_t {
	COMMAND_PING = 1,
	COMMAND_ECHO = 2
};

enum status_t {
	STATUS_OK = 0,
	STATUS_UNKNOWN_COMMAND = 1,
	STATUS_MISSING_DATA = 2
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
		default: // Unknown command
			uart_put_uint8(STATUS_UNKNOWN_COMMAND);
	}
}
