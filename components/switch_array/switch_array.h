#pragma once
#include "esphome.h"
#include "esphome/components/gpio/binary_sensor/gpio_binary_sensor.h"
#include <vector>

namespace esphome {
  namespace switch_array {

    class SwitchArray;

    class SwitchArrayTrigger : public Trigger<int> {
    public:
      SwitchArrayTrigger(SwitchArray *parent);
    };

    class SwitchArray : public Component {
    public:
      // Now accepts the generated name string
      void add_pin(InternalGPIOPin *pin, const std::string &name) {
        auto *sensor = new gpio::GPIOBinarySensor();
        sensor->set_pin(pin);

        // If a name was generated, apply it and register it with the core App
        if (!name.empty()) {
          sensor->set_name(name.c_str());
          sensor->name_ = name;
          App.register_binary_sensor(sensor);
        }

        int index = this->sensors_.size();

        // Listen for state changes (button press)
        sensor->add_on_state_callback([this, index](bool state) {
          if (state) {
            for (auto *trigger : this->triggers_) {
              trigger->trigger(index);
            }
          }
        });

        this->sensors_.push_back(sensor);
      }

      void add_trigger(SwitchArrayTrigger *trigger) {
        this->triggers_.push_back(trigger);
      }

      void setup() override {
        for (auto *sensor : this->sensors_) {
          sensor->setup();
        }
      }

      void loop() override {
        for (auto *sensor : this->sensors_) {
          sensor->loop();
        }
      }

    protected:
      std::vector<gpio::GPIOBinarySensor *> sensors_;
      std::vector<SwitchArrayTrigger *> triggers_;
    };

    inline SwitchArrayTrigger::SwitchArrayTrigger(SwitchArray *parent) {
      parent->add_trigger(this);
    }

  }  // namespace switch_array
}  // namespace esphome
