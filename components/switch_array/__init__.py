import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import pins
from esphome import automation
from esphome.const import CONF_ID, CONF_TRIGGER_ID, CONF_NAME

AUTO_LOAD = ['gpio', 'binary_sensor']

switch_array_ns = cg.esphome_ns.namespace('switch_array')
SwitchArray = switch_array_ns.class_('SwitchArray', cg.Component)
SwitchArrayTrigger = switch_array_ns.class_('SwitchArrayTrigger', automation.Trigger.template(cg.int_))

CONF_PINS = 'pins'
CONF_ON_KEY = 'on_key'

# Custom validator to automatically inject PULLUP and inverted logic
def validate_pin(value):
    # If the user just provides a number (e.g., 7), convert it to a dict
    if isinstance(value, (int, str)):
        value = {'number': value}

    # Inject defaults if they aren't explicitly overridden in the YAML
    if isinstance(value, dict):
        value = value.copy()
        if 'mode' not in value:
            value['mode'] = 'INPUT_PULLUP'
        if 'inverted' not in value:
            value['inverted'] = True

    # Pass the modified dict to ESPHome's strict internal pin validator
    return pins.internal_gpio_input_pin_schema(value)

# Define the schema for a single array
SWITCH_ARRAY_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(SwitchArray),
    cv.Optional(CONF_NAME): cv.string, # Base name for generating sensor names
    cv.Required(CONF_PINS): cv.All(cv.ensure_list(validate_pin)),
    cv.Optional(CONF_ON_KEY): automation.validate_automation({
        cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(SwitchArrayTrigger),
    }),
}).extend(cv.COMPONENT_SCHEMA)

# Allow multiple arrays
CONFIG_SCHEMA = cv.All(cv.ensure_list(SWITCH_ARRAY_SCHEMA))

async def to_code(config):
    for conf in config:
        var = cg.new_Pvariable(conf[CONF_ID])
        await cg.register_component(var, conf)

        # Grab the base name, default to empty string if not provided
        base_name = conf.get(CONF_NAME, "")

        for i, pin_config in enumerate(conf[CONF_PINS]):
            pin = await cg.gpio_pin_expression(pin_config)

            # Generate a dynamic name (e.g., "Menu Keypad Button 0")
            sensor_name = f"{base_name} Button {i}" if base_name else ""

            # Pass both the pin and the generated name to C++
            cg.add(var.add_pin(pin, sensor_name))

        for trigger_conf in conf.get(CONF_ON_KEY, []):
            trigger = cg.new_Pvariable(trigger_conf[CONF_TRIGGER_ID], var)
            await automation.build_automation(trigger, [(cg.int_, 'pos')], trigger_conf)
