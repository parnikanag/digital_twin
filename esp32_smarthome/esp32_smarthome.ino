/*
 * ================================================================
 *  ESP32 — Bedroom 1 Digital Twin
 *
 *  PIN MAP:
 *    GPIO 5  → Lamp   LED         (output)
 *    GPIO 18 → AC     LED         (output)
 *    GPIO 19 → Geyser LED         (output)
 *    GPIO 23 → Fridge LED         (output)
 *    GPIO 13 → Servo  signal      (output)
 *    GPIO 4  → Reed switch        (INPUT_PULLUP)
 *                LOW  = door CLOSED (magnet present)
 *                HIGH = door OPEN   (magnet removed)
 *
 *  /device/state JSON keys read by this sketch:
 *    lights_on, ac_on, geyser_on, fridge_on, servo_angle
 *
 *  Endpoints used:
 *    GET  /device/state       poll every 1 s  → apply to GPIOs
 *    POST /sensor/push        every 5 s       → temp/humidity/smoke/motion
 *    POST /sensor/fridge-door on reed change  → immediate door status update
 *
 *  Serial commands (115200 baud, line ending = Newline):
 *    LAMP ON / LAMP OFF
 *    AC ON   / AC OFF
 *    GEYSER ON / GEYSER OFF
 *    FRIDGE ON / FRIDGE OFF
 *    DOOR OPEN / DOOR CLOSE
 * ================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// ── WiFi ──────────────────────────────────────────────────────────────────────
const char* WIFI_SSID = "PN";
const char* WIFI_PASS = "pari@2005";

// ── Backend base URL ──────────────────────────────────────────────────────────
const char* BASE_URL        = "http://10.194.5.85:8000";
// Individual endpoints (built from BASE_URL at setup)
char STATE_URL[64];
char PUSH_URL[64];
char FRIDGE_DOOR_URL[64];

// ── Output pins ───────────────────────────────────────────────────────────────
#define LAMP_PIN    5
#define AC_PIN      18
#define GEYSER_PIN  19
#define FRIDGE_PIN  23
#define SERVO_PIN   13

// ── Input pins ────────────────────────────────────────────────────────────────
#define REED_PIN    4   // INPUT_PULLUP — LOW=closed, HIGH=open

// ── Objects ───────────────────────────────────────────────────────────────────
Servo doorServo;

// ── Device state (mirrors what backend holds) ─────────────────────────────────
bool state_lamp        = false;
bool state_ac          = false;
bool state_geyser      = false;
bool state_fridge      = false;
bool door_open         = false;   // false=0°  true=90°
bool fridge_door_open  = false;   // reed switch reading

// ── Timers ────────────────────────────────────────────────────────────────────
unsigned long lastPoll       = 0;
unsigned long lastPush       = 0;
const unsigned long POLL_MS  = 1000;   // poll /device/state every 1 s
const unsigned long PUSH_MS  = 5000;   // push sensor data every 5 s

// =============================================================================
//  SETTERS — each one drives the GPIO and prints to Serial Monitor
// =============================================================================

void setLamp(bool on) {
  if (state_lamp == on) return;
  state_lamp = on;
  digitalWrite(LAMP_PIN, on ? HIGH : LOW);
  Serial.println("-----------------------------");
  Serial.println(on ? ">>> LAMP ON  <<<" : ">>> LAMP OFF <<<");
  Serial.println("-----------------------------");
}

void setAC(bool on) {
  if (state_ac == on) return;
  state_ac = on;
  digitalWrite(AC_PIN, on ? HIGH : LOW);
  Serial.println("-----------------------------");
  Serial.println(on ? ">>> AC ON  <<<" : ">>> AC OFF <<<");
  Serial.println("-----------------------------");
}

void setGeyser(bool on) {
  if (state_geyser == on) return;
  state_geyser = on;
  digitalWrite(GEYSER_PIN, on ? HIGH : LOW);
  Serial.println("-----------------------------");
  Serial.println(on ? ">>> GEYSER ON  <<<" : ">>> GEYSER OFF <<<");
  Serial.println("-----------------------------");
}

void setFridge(bool on) {
  if (state_fridge == on) return;
  state_fridge = on;
  digitalWrite(FRIDGE_PIN, on ? HIGH : LOW);
  Serial.println("-----------------------------");
  Serial.println(on ? ">>> FRIDGE ON  <<<" : ">>> FRIDGE OFF <<<");
  Serial.println("-----------------------------");
}

void setDoor(bool open_pos) {
  if (door_open == open_pos) return;
  door_open = open_pos;
  doorServo.write(open_pos ? 90 : 0);
  Serial.println("-----------------------------");
  Serial.println(open_pos ? ">>> DOOR OPEN  (90 deg) <<<" : ">>> DOOR CLOSED (0 deg) <<<");
  Serial.println("-----------------------------");
}

// =============================================================================
//  SERIAL COMMANDS
// =============================================================================

void handleSerial() {
  if (!Serial.available()) return;
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  cmd.toUpperCase();
  if      (cmd == "LAMP ON")    setLamp(true);
  else if (cmd == "LAMP OFF")   setLamp(false);
  else if (cmd == "AC ON")      setAC(true);
  else if (cmd == "AC OFF")     setAC(false);
  else if (cmd == "GEYSER ON")  setGeyser(true);
  else if (cmd == "GEYSER OFF") setGeyser(false);
  else if (cmd == "FRIDGE ON")  setFridge(true);
  else if (cmd == "FRIDGE OFF") setFridge(false);
  else if (cmd == "DOOR OPEN")  setDoor(true);
  else if (cmd == "DOOR CLOSE") setDoor(false);
  else Serial.println("Unknown. Use: LAMP/AC/GEYSER/FRIDGE ON|OFF  DOOR OPEN|CLOSE");
}

// =============================================================================
//  POLL /device/state — apply dashboard commands to GPIOs
// =============================================================================

bool pollDashboard() {
  if (WiFi.status() != WL_CONNECTED) return false;

  HTTPClient http;
  http.begin(STATE_URL);
  http.setTimeout(2000);
  int code = http.GET();
  bool changed = false;

  if (code == 200) {
    String body = http.getString();
    StaticJsonDocument<256> doc;
    if (!deserializeJson(doc, body)) {

      // ── Read keys that match exactly what the backend returns ──────────────
      bool want_lamp   = doc["lights_on"]   | false;
      bool want_ac     = doc["ac_on"]       | false;
      bool want_geyser = doc["geyser_on"]   | false;   // ← was fan_on — now geyser_on
      bool want_fridge = doc["fridge_on"]   | false;
      int  raw_angle   = doc["servo_angle"] | 0;
      bool want_door   = (raw_angle == 90);

      if (want_lamp   != state_lamp)   { setLamp(want_lamp);     changed = true; }
      if (want_ac     != state_ac)     { setAC(want_ac);         changed = true; }
      if (want_geyser != state_geyser) { setGeyser(want_geyser); changed = true; }
      if (want_fridge != state_fridge) { setFridge(want_fridge); changed = true; }
      if (want_door   != door_open)    { setDoor(want_door);     changed = true; }

      if (!changed) {
        Serial.printf("Poll OK — Lamp:%d AC:%d Geyser:%d Fridge:%d Door:%d\n",
                      state_lamp, state_ac, state_geyser, state_fridge, door_open);
      }
    } else {
      Serial.println("Poll: JSON parse error");
    }
  } else {
    Serial.printf("Poll failed: HTTP %d\n", code);
  }

  http.end();
  return changed;
}

// =============================================================================
//  PUSH /sensor/fridge-door — called immediately on reed-switch change
// =============================================================================

void pushFridgeDoor(bool is_open) {
  if (WiFi.status() != WL_CONNECTED) return;

  StaticJsonDocument<64> doc;
  doc["room"]             = "Bedroom 1";
  doc["fridge_door_open"] = is_open;
  String body;
  serializeJson(doc, body);

  HTTPClient http;
  http.begin(FRIDGE_DOOR_URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(3000);
  int code = http.POST(body);
  Serial.printf("Fridge door push → HTTP %d\n", code);
  http.end();
}

// =============================================================================
//  PUSH /sensor/push — full sensor data every 5 s
// =============================================================================

void pushSensors(float temp, float hum, int smoke, bool motion) {
  if (WiFi.status() != WL_CONNECTED) return;

  bool  smokeAlert = (smoke > 3000);
  float power_w    = (state_lamp   ?   40.0f : 0)
                   + (state_ac     ? 1200.0f : 0)
                   + (state_geyser ? 2000.0f : 0)
                   + (state_fridge ?  150.0f : 0);

  StaticJsonDocument<512> doc;
  doc["room"]             = "Bedroom 1";
  doc["appliance"]        = "ESP32-Bedroom1";
  doc["power_w"]          = power_w;
  doc["temp_c"]           = temp;
  doc["is_on"]            = (state_lamp || state_ac || state_geyser || state_fridge);
  doc["humidity"]         = hum;
  doc["smoke_ppm"]        = smoke;
  doc["smoke_alert"]      = smokeAlert;
  doc["motion"]           = motion;
  doc["fridge_door_open"] = fridge_door_open;

  String body;
  serializeJson(doc, body);

  HTTPClient http;
  http.begin(PUSH_URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);
  int code = http.POST(body);
  Serial.printf("Sensor push → HTTP %d\n", code);
  http.end();
}

// =============================================================================
//  SETUP
// =============================================================================

void setup() {
  Serial.begin(115200);
  delay(500);

  // Build URLs from base
  snprintf(STATE_URL,       sizeof(STATE_URL),       "%s/device/state",        BASE_URL);
  snprintf(PUSH_URL,        sizeof(PUSH_URL),         "%s/sensor/push",         BASE_URL);
  snprintf(FRIDGE_DOOR_URL, sizeof(FRIDGE_DOOR_URL),  "%s/sensor/fridge-door",  BASE_URL);

  // Output pins
  int outPins[] = {LAMP_PIN, AC_PIN, GEYSER_PIN, FRIDGE_PIN};
  for (int p : outPins) { pinMode(p, OUTPUT); digitalWrite(p, LOW); }

  // Servo
  doorServo.setPeriodHertz(50);
  doorServo.attach(SERVO_PIN, 500, 2400);
  doorServo.write(0);

  // Reed switch
  pinMode(REED_PIN, INPUT_PULLUP);

  // WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println();

  Serial.println("================================");
  Serial.println("  ESP32  BEDROOM 1 DIGITAL TWIN");
  Serial.println("================================");
  Serial.print("IP: ");       Serial.println(WiFi.localIP());
  Serial.print("Backend: ");  Serial.println(BASE_URL);
  Serial.println("Polling /device/state every 1 s");
  Serial.println("Commands: LAMP/AC/GEYSER/FRIDGE ON|OFF  DOOR OPEN|CLOSE");
  Serial.println("================================");
}

// =============================================================================
//  LOOP
// =============================================================================

void loop() {
  unsigned long now = millis();

  // 1. Serial commands — always instant
  handleSerial();

  // 2. Reed switch — check every loop, push immediately on change
  bool reed = (digitalRead(REED_PIN) == HIGH);  // HIGH = open (no magnet)
  if (reed != fridge_door_open) {
    fridge_door_open = reed;
    Serial.println("-----------------------------");
    Serial.println(fridge_door_open ? ">>> FRIDGE DOOR OPEN  <<<" : ">>> FRIDGE DOOR CLOSED <<<");
    Serial.println("-----------------------------");
    pushFridgeDoor(fridge_door_open);   // push immediately, don't wait 5 s
  }

  // 3. Poll dashboard every 1 s — apply any button clicks to GPIOs
  if (now - lastPoll >= POLL_MS) {
    lastPoll = now;
    bool changed = pollDashboard();
    if (changed) {
      // Push sensor data right away so dashboard shows updated device state
      pushSensors(25.0, 60.0, 0, false);   // placeholder values on immediate push
      lastPush = now;
    }
  }

  // 4. Full sensor push every 5 s
  if (now - lastPush >= PUSH_MS) {
    lastPush = now;

    // ── Read sensors ──────────────────────────────────────────────────────────
    // If you have DHT22 connected, replace these with real reads:
    //   float temp = dht.readTemperature();
    //   float hum  = dht.readHumidity();
    // For now using fixed values so the sketch compiles without DHT library:
    float temp  = 25.0;
    float hum   = 60.0;
    int   smoke = analogRead(34);      // MQ2 on GPIO34
    bool  pir   = digitalRead(27);     // PIR on GPIO27

    Serial.println("========== STATUS ==========");
    Serial.printf("Temp:%.1fC  Hum:%.0f%%  MQ2:%d  Smoke:%s  Motion:%s\n",
                  temp, hum, smoke,
                  smoke > 3000 ? "ALERT" : "Clear",
                  pir ? "YES" : "NO");
    Serial.printf("FridgeDoor:%s\n", fridge_door_open ? "OPEN" : "CLOSED");
    Serial.printf("Lamp:%s  AC:%s  Geyser:%s  Fridge:%s  Door:%s\n",
                  state_lamp   ? "ON" : "OFF",
                  state_ac     ? "ON" : "OFF",
                  state_geyser ? "ON" : "OFF",
                  state_fridge ? "ON" : "OFF",
                  door_open    ? "OPEN" : "CLOSED");
    Serial.println("============================");

    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi lost — reconnecting...");
      WiFi.reconnect();
      delay(3000);
      return;
    }

    pushSensors(temp, hum, smoke, pir);
  }
}
