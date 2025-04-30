import time, json, keyboard, mouse
from threading import Thread

class BGSI_Recorder:
    def __init__(self, recorded: dict = None, stop_key: str = 'f2'):
        self.start_time = None
        self.stop_recording_flag = False
        self.play_start_time = None
        self.is_playing = False
        self.speed_factor = 1
        self.stop_key = stop_key

        self.recorded = recorded if recorded else {
            'keyboard': [],
            'mouse': []
        }

    def record(self, countdown: float = 0.001):
        self.stop_recording_flag = False
        self.recorded = {
            'keyboard': [],
            'mouse': []
        }
        self.start_time = time.time() + countdown
        print("Recording started...")

        # Start listeners in separate threads to avoid blocking
        mouse_listener_thread = Thread(target=self.mouse_listener)
        keyboard_listener_thread = Thread(target=self.keyboard_listener)

        mouse_listener_thread.start()
        keyboard_listener_thread.start()


    def play(self, countdown: float = 0.001, speed_factor: float = 1, only_essential_moves: bool = False, macro_path: str = None):
        if macro_path: self.load(macro_path)
        self.is_playing = True

        if speed_factor > 5:
            speed_factor = 5

        if only_essential_moves:
            self.filter_moves()

        self.speed_factor = speed_factor
        self.play_start_time = time.time() + countdown

        #mouse_ = Thread(target=self.play_mouse, args=(self.recorded['mouse'],))
        keyboard_ = Thread(target=self.play_keyboard, args=(self.recorded['keyboard'],))
        stop_thread = Thread(target=self.stop_player_listener)
        stop_thread.daemon = True
        stop_thread.start()


        #mouse_.start()
        keyboard_.start()
        #mouse_.join()
        keyboard_.join()

        self.is_playing = False

    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump(self.recorded, f, indent=4)

    def load(self, path: str):
        with open(path, 'r') as f:
            self.recorded = json.load(f)

    def keyboard_listener(self):
        self.wait_to_start(self.start_time)
        print(f"Keyboard listener started. Press '{self.stop_key}' to stop recording.")
        
        def on_key_event(event: keyboard.KeyboardEvent):
            if self.stop_recording_flag: return
            
            # Check for stop key
            if event.name == self.stop_key and event.event_type == keyboard.KEY_DOWN:
                print(f"'{self.stop_key}' pressed. Stopping recording.")
                self.stop_recording() # This will set flag and unhook
                return # Don't record the stop key itself

            # Record event relative to start time
            # recording has actually started ?
            if self.start_time is not None and event.time >= self.start_time:
                 timestamp = event.time - self.start_time
                 print(f"  Recording KB Event: ['{event.event_type == keyboard.KEY_DOWN}', '{event.name}', {timestamp:.4f}]")
                 self.recorded['keyboard'].append([
                      event.event_type == keyboard.KEY_DOWN,
                      event.name,
                      timestamp
                 ])

        try:
            # Hook the callback
            keyboard.hook(on_key_event) # Keep the listener thread alive until stop_recording is called
            while not self.stop_recording_flag: time.sleep(0.1)
                
        except Exception as e:
            print(f"Error in keyboard listener: {e}")
        finally:
            # Ensure the hook is removed if the thread exits unexpectedly,
            # though stop_recording should normally handle it.
            try:
                 keyboard.unhook(on_key_event)
            except Exception as e:
                 pass
            print("Keyboard listener finished.")


    # Mouse listener needs to run until unhooked
    def mouse_listener(self):
        self.wait_to_start(self.start_time)
        print("Mouse listener started.")
        try:
            mouse.hook(self.on_callback)
            while not self.stop_recording_flag: time.sleep(0.1)
        except Exception as e:
             print(f"Error setting up mouse hook: {e}") # May need admin rights..? right?
        finally:
             print("Mouse listener finished.")


    def on_callback(self, event):
        if self.start_time is None or time.time() < self.start_time:
             return
         
        if self.stop_recording_flag:
             return

        timestamp = time.time() - self.start_time

        if isinstance(event, mouse.MoveEvent):
            self.recorded['mouse'].append(['move', event.x, event.y, timestamp])

        elif isinstance(event, mouse.ButtonEvent):
            self.recorded['mouse'].append(['click', event.button, event.event_type == 'down', timestamp])

        elif isinstance(event, mouse.WheelEvent):
            self.recorded['mouse'].append(['scroll', event.delta, timestamp])

    def stop_recording(self, action_name):
        if not self.stop_recording_flag:
            print("Executing stop_recording...")
            self.stop_recording_flag = True
            
            try:
                mouse.unhook(self.on_callback)
                print("Mouse unhooked.")
            except Exception as e:
                print(f"Warning: Error unhooking mouse: {e}")
            try:
                keyboard.unhook_all()
                print("All keyboard hooks removed.")
            except Exception as e:
                print(f"Warning: Error unhooking keyboard: {e}")

            time.sleep(0.1)
            print("stop_recording finished.")
            
            # Save the recorded data to a JSON file (also load it for replay later)
            self.save(f"{action_name}.json")
            return self.recorded


    def play_keyboard(self, key_events: list):
        self.wait_to_start(self.play_start_time)
        pressed_keys = set()

        for i, key in enumerate(key_events):
            if not self.is_playing:
                print(f"play_keyboard: Stopping playback early (event {i}).")
                break

            pressed, scan_code, t = key

            # Calculate adjusted time based on speed factor
            adjusted_time = t / self.speed_factor
            current_playback_time = time.time() - self.play_start_time
            time_to_wait = adjusted_time - current_playback_time

            #print(f"  KB Play Event {i}: Data={key}, Orig_t={t:.4f}, Adj_t={adjusted_time:.4f}, Wait={time_to_wait:.4f}")

            if time_to_wait > 0:
                slept = 0
                interval = 0.01  # 10ms
                while slept < time_to_wait:
                    if not self.is_playing:
                        print(f"play_keyboard: Stopping playback early during wait (event {i}).")
                        break
                    sleep_time = min(interval, time_to_wait - slept)
                    time.sleep(sleep_time)
                    slept += sleep_time
                if not self.is_playing:
                    break

            if not self.is_playing:
                print(f"play_keyboard: Stopping playback early after sleep (event {i}).")
                break

            try:
                action_str = "Press" if pressed else "Release"
                #print(f"    -> {action_str} '{scan_code}'")
                if pressed:
                    keyboard.press(scan_code)
                    pressed_keys.add(scan_code)
                else:
                    keyboard.release(scan_code)
                    pressed_keys.discard(scan_code)
            except Exception as e:
                print(f"Error playing keyboard event ({action_str} {scan_code}): {e}")

        if pressed_keys:
            print(f"Releasing all pressed keys: {pressed_keys}")
            for scan_code in list(pressed_keys):
                try:
                    keyboard.release(scan_code)
                except Exception as e:
                    print(f"Error releasing key {scan_code}: {e}")

        print("play_keyboard finished.")


    def play_mouse(self, mouse_events: list):
        self.wait_to_start(self.play_start_time)

        for mouse_event in mouse_events:
            event_type, *args, t = mouse_event

            # Calculate adjusted time based on speed factor
            adjusted_time = t / self.speed_factor
            current_playback_time = time.time() - self.play_start_time
            time_to_wait = adjusted_time - current_playback_time

            if time_to_wait > 0:
                time.sleep(time_to_wait)

            if not self.is_playing:break

            try:
                if event_type == 'move':
                    mouse.move(*args)
                elif event_type == 'click':
                    button, is_press = args
                    if is_press:
                        mouse.press(button)
                    else:
                        mouse.release(button)
                elif event_type == 'scroll':
                    delta = args[0]
                    mouse.wheel(delta)
            except Exception as e:
                 print(f"Error playing mouse event ({event_type} {args}): {e}")

    @staticmethod
    def wait_to_start(t: float):
        time_to_sleep = t - time.time()
        if time_to_sleep > 0:
            time.sleep(time_to_sleep)

    def stop_player_listener(self):
        print(f"Playback stop listener started. Press '{self.stop_key}' to stop.")
        keyboard.wait(self.stop_key)
        if self.is_playing:
             print(f"'{self.stop_key}' pressed during playback. Stopping player...")
             self.is_playing = False
             
    def filter_moves(self):
        if not self.recorded['mouse']: return

        filtered_moves = []
        last_event = None

        # Always keep the first event if it's a move
        if self.recorded['mouse'][0][0] == 'move':
             filtered_moves.append(self.recorded['mouse'][0])
             last_event = self.recorded['mouse'][0]
             start_index = 1
        else:
             start_index = 0


        for i in range(start_index, len(self.recorded['mouse'])):
            current_event = self.recorded['mouse'][i]

            # If current is not a move, keep it
            if current_event[0] != 'move':
                if last_event and last_event[0] == 'move':
                    # Avoid adding duplicate non-move events if last_event was also non-move
                    if not filtered_moves or filtered_moves[-1] != last_event: filtered_moves.append(last_event)
                    
                filtered_moves.append(current_event)

            # Update last_event regardless of type
            last_event = current_event

        # Ensure the very last event is added if it was a move and loop finished
        if last_event and last_event[0] == 'move':
             if not filtered_moves or filtered_moves[-1] != last_event:
                  filtered_moves.append(last_event)


        print(f"Filtered mouse events from {len(self.recorded['mouse'])} to {len(filtered_moves)}")
        self.recorded['mouse'] = filtered_moves
