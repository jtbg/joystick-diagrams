import logging

from joystick_diagrams.input.input import Input_

_logger = logging.getLogger("__name__")


class Device_:
    def __init__(self, guid: str, name: str):
        self.guid = guid.strip().lower()
        self.name = name.strip()
        self.inputs: dict[str, Input_] = {}

    def create_input(self, input_id: str, command: str) -> None:
        input = self.get_input(input_id)

        if input:
            input.command = command
            _logger.debug(f"Input {input_id} already exists on {self} and will be overwritten")
        else:
            _logger.debug(f"Input {input_id} added to  {self}")
            self.inputs[input_id] = Input_(input_id, command)

    def get_input(self, input_id: str) -> Input_ | None:
        return self.inputs.get(input_id)

    def add_modifier_to_input(self, input_id, modifier: set, command: str) -> None:
        """
        Adds a modifier to an input if it exists
        """

        _logger.debug(f"Adding modifier {modifier} to input {input_id}")
        input = self.get_input(input_id)

        if input is None:
            _logger.warning(
                f"Modifier attempted to be added to {input_id} but input does not exist. So a shell will be created"
            )
            self.create_input(input_id, "")

            shell_input = self.get_input(input_id)

            if shell_input:
                shell_input.add_modifier(modifier, command)

        else:
            input.add_modifier(modifier, command)


if __name__ == "__main__":
    dev = Device_("guid1", "Potato")

    dev.create_input("button_1", "shoot")

    print(dev.inputs)

    dev.add_modifier_to_input("button_1", {"ctrl", "alt"}, "pickup")
    dev.add_modifier_to_input("button_2", {"ctrl", "alt"}, "pickup")
    dev.add_modifier_to_input("button_1", {"alt", "ctrl"}, "pickup")
    dev.add_modifier_to_input("button_1", {"spacebar", "ctrl"}, "dunk")

    for i in dev.inputs.values():
        print(i.identifier)
        print(i.command)
        print(i.modifiers)
