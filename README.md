
# VeadoSC

VeadoSC is a [StreamController](https://streamcontroller.github.io/docs/latest/) plugin for managing PNGTuber avatars in [veadotube](https://veado.tube/).

## Installation

VeadoSC is not yet a part of the StreamController store. VeadoSC can be installed as a custom plugin by directly adding this repository to StreamController.

1. From the StreamController main screen, click the hamburger menu and select `Open Settings`
2. Select the `Store` tab.
3. Enable `Custom Plugins`, then click the `+` button in the `Custom Plugins` row.
4. Enter this repository (`https://github.com/Kekemui/VeadoSC`) and use the `main` branch.
5. Finally, open the plugin store as usual  (hamburger > `Open Store`), find VeadoSC, and click the `install` button.

### Configuration

VeadoSC requires a static websocket port in veadotube. To configure a static port, use the following steps:

1. In veadotube, open the `Program Settings` flyout (left side, looks like an application window with a cursor)
2. In the `server address` row, include a port along with localhost, like the following: `localhost:40404`. You can use any port between 1024-65535, not withstanding any port currently in use by your computer.
3. **Remember this port**.

Next, add a VeadoSC action in StreamController:

1. Select a button where you'd like to control veadotube. Add the SetState action.
2. In the action configuration, set the "Veadotube IP Address" to the server (this is almost certainly `localhost`).
3. Set the "Veadotube Static Port" to the port you used earlier (`40404` if you followed the example verbatim).
4. Finally, set the "State Name" you'd like to use for this button.
  * For additional buttons, you only need to set this "State Name".

## Acknowledgements

* StreamController and the StreamController plugin kit is owned by 'Core447', see the [StreamController docs](https://streamcontroller.github.io/docs/latest/) for more information.
* veadotube is developed by [olmewe](https://olmewe.com/) and [BELLA!](https://bellaexclamation.art/). VeadoSC works with veadotube, but is otherwise unassociated with the veadotube project. See [veadotube](https://veado.tube) for more information.
