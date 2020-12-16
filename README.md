# Alfred The Melee AI
---
This repository acts as the **developmental** version of Alfred and not the offical **main** release. Official documentation hasn't been written, however the requirements and initial setup for Alfred has been provided.

## Alfred
1. [Brief Overview](#brief-overview)
2. [Test Stacks](#test-stacks)
3. [Requirements](#requirements)
4. [Initial Setup](#initial-setup) 
5. [Alfred Commands](#alfred-commands)
6. [Debugging](#debugging)
7. [Progress Table](#progress-table)

### Brief Overview
Alfred has been designed to incorporate fast communication from [Alfred's Dolphin] to a back-end framework that collects data either from *live emulations* or *offline replays*. This is collected and brought together within the manager where data is fed to the environment in order to train and predict a players decisions (controller state) for a specific reaction.

### Test Stacks
|Operating System|RAM|CPU|GPU|Cuda Cores|
|:-------------|:-------------|:-------------|:-------------|:-------------|
|Windows 10|16GB|[Intel i7 - 4GHz](https://ark.intel.com/content/www/us/en/ark/products/88195/intel-core-i7-6700k-processor-8m-cache-up-to-4-20-ghz.html)|[Nvidia GTX 1070 8GB](https://www.nvidia.com/en-us/geforce/products/10series/wheretobuy/geforce-gtx-1070/)|2048|
|Ubuntu 18.04|16GB|[AMD Ryzen 7 3700X](https://www.amd.com/en/products/cpu/amd-ryzen-7-3700x)|[Nvidia GTX 1660 3GB](https://www.nvidia.com/en-us/geforce/news/nvidia-geforce-gtx-1660/)|1408|
|Ubuntu 20.04|16GB|[AMD Ryzen 7 3700X](https://www.amd.com/en/products/cpu/amd-ryzen-7-3700x)|[Nvidia GTX 1660 3GB](https://www.nvidia.com/en-us/geforce/news/nvidia-geforce-gtx-1660/)|1408|

### Requirements
|Program|Version|Installation|Notes|
|:-------------|:-------------|:-------------|:-------------|
|Python|3.8.5|conda create -n meleeai python=3.8.5 pip|>3.8.5 hasn't been tested.|

### Initial Setup
Alfred may be ran indepent of the system an instance of the Alfred Dolphin emulator is running on. The motivation behind this was to ensure Alfred may be trained live and process large sets of data without bogging down the emulator. 
1. Ensure you have the latest release of [Alfred's Dolphin] emulator.
2. Change the Dolphin.cfg SendingAddress to the address you wish to send the data to.
3. Ensure the target machine's IP is known before sending. **Caution:** Running the emulator will flood the network with high amounts of traffic. Make sure your host machine, target machine, and router are configured properly to accept incoming/outcoming data. 
4. **Important:** On Windows the Dolphin executable is more than likely using Documents\Dolphin_Emulator. If you have more than one instance of Dolphin, ensure Alfred is configured for Slippi Recording. To check, right-click the game inside [Alfred's Dolphin] emulator and ensure the Gecko Codes are set for Netplay Settings, Performance, Game Audio On/Off (Your choice), and Slippi Recording.

### Alfred Commands
```sh
meleeai.utils.flags:
  --alfred_port: Alfred port that's dedicated to the agent.
    (default: '0')
    (an integer)
  --burnouttime: Time to wait until offline emulation has completed a slippi playback. Used when End frame is either missed, dropped, or merely not sent.
    (default: '10000')
    (an integer)
  --controllerport: Controller port sending to Alfred.
    (default: '55079')
    (an integer)
  --[no]display: Displays Alfred's GUI.
    (default: 'false')
  --display_queuesize: Queue size regarding the display gui.
    (default: '10')
    (an integer)
  --emulator: Alfred Ishiiruka Slippi emulator with socket implementation. Playback MUST be setup if this choice is used.
    (default: './Ishiiruka/bin/dolphin')
  --gc_ports: Number of gamecube ports on the system.
    (default: '4')
    (an integer)
  --[no]live_emulation: If the training for alfred should be conducted on a live session.
    (default: 'false')
  --melee_iso: Melee ISO location.
    (default: './Melee/')
  --memorysize: Buffer data to hold till consumed.
    (default: '1000')
    (an integer)
  --min_frame_length: Minimum frame length required to run the emulation.
    (default: '1500')
    (an integer)
  --min_slippi_version: Minimum slippi version able to be parsed.
    (default: '2.0.0')
  --[no]no_lras: Ignore slippi recordings that end with LRA+START.
    (default: 'true')
  --opponent_character_id: Character ID associated by Slippi, view slippi.id.CSSCharacter for more details.
    (default: '20')
    (an integer)
  --player_character_id: Character ID associated by Slippi, view slippi.id.CSSCharacter for more details.
    (default: '0')
    (an integer)
  --player_costume_id: Costume ID associated by Slippi (0 = Default).
    (default: '4')
    (an integer)
  --playerport: Starting player port 0, any subsequence is 55082 + n.
    (default: '55082')
    (an integer)
  --prediction_tick_rate: 1/60th of a frame at which a prediction should occur.
    (default: '0.016')
    (a number)
  --sending_ip: IP address to send processed controller state data to Dolphin client.
    (default: '127.0.0.1')
  --slippi_data: Slippi data to run the emulator ontop of if offline.
    (default: './data/')
  --slippi_end_byte: End byte (57) for slippi end data.
    (default: '2')
    (an integer)
  --slippi_post_byte: Post frame byte (56) for post-frame data.
    (default: '52')
    (an integer)
  --slippi_pre_byte: Pre frame byte (55) for pre-frame data.
    (default: '64')
    (an integer)
  --slippi_start_byte: Start byte (54) for slippi start data.
    (default: '418')
    (an integer)
  --slippiport: Slippi port sending to Alfred.
    (default: '55080')
    (an integer)
  --stage_id: Stage ID associated by Slippi, view slippi.id.Stage for more details.
    (default: '31')
    (an integer)
  --[no]train: Runs the training part of the engine.
    (default: 'false')
  --videoport: Video port sending to Alfrd.
    (default: '55081')
    (an integer)
```

### Debugging
Alfred is still in the making and is bound to have its fair share of bugs, please use with caution.
**Common Issues & Resolutions**
- My Windows machine isn't receiving any messages, I've used wireshark and the messages are being blocked.
    > Make sure network discovery is on, I found this early on that Windows would block any of the UDP messages from Dolphin or Alfred.
- My emulator isn't recording!
    > Make sure all the settings within the emulator itself and the Melee ISO match! A great comparison is the Dolphin emulator that comes with the Slippi desktop app.
- I DoS'd myself! How could this happen and how do I fix it?
    > The emulator sends Controller, Slippi, and Video data all at once which is sure to DoS your network by overloading your router or receiving device. Ensure that your router supports 20Mb/s traffic.
- The receive rate from the emulator to Alfred is slow!
    > This can be one of many things, begin checking that for the most optimal experience that your connected via Ethernet. Make sure your router doesn't automatically throttle traffic, I haven't experienced a case where this was the issue. If this still continues contact Abszol.

## Progress Table
| Task        | Status           | Dated Last Updated |
|:-------------|:-------------:| :-------------: |
| Load dumped data into Alfred | Done | 12/15/2020 |
| Have display fully functional with controller info | Postponed | 12/15/2020 |
| Evaluate OpenAI gym and self imitation learning | In Process | 12/15/2020 |
| Write correlator between two sockets receiving data | Complete | 07/15/2020 |
| Modify Kalman to accept all controller features | In Progress | 07/15/2020 |
| Write training model | Not Started | 03/01/2020 |
| Translate model output to controller state | Not Started | 03/01/2020 |

   [alfred's dolphin]: <https://github.com/iamabszol/ishiiruka>

