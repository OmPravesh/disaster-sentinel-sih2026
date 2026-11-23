# Disaster Sentinel — 60-second 3D explainer (storyboard v1)

**Format:** 1080×1920 vertical, 30 fps, 60 s (1800 frames), Blender + EEVEE
**Look:** stylized low-poly cartoon (like the "+50% IQ" reference): soft light, bright colors,
bold white/yellow titles with a dark outline, a pill-shaped HUD at the top, and captions that
appear word by word in the middle of the screen.
**Audio:** English voiceover (macOS Indian-English voice) + sound effects (rain, river, fire crackle, radio ping, phone buzz, siren).

## The pattern copied from the references
- **Hook title** in the first 2 s ("WHAT IF …?"), big, two colors.
- **HUD pinned at the top** for the whole video, with numbers that change as the story moves:
  `UTTARAKHAND · 2:14 AM` | `WARNING TIME 0 min` → `60 min` | `PEOPLE SAFE 0` → `1,240`.
- **A cut every 2–4 s.** Camera always moving slightly: slow push-in, orbit, or follow.
  Never a static frame.
- **Overlapping motion.** Objects never start and stop together: rain starts before the river rises,
  people turn their heads before they walk, and the pop-ins overshoot and settle (back-out ease).
- **Rewind beat** (`◀◀ REWIND`) like the "Remember every second" video: we show the disaster
  first, then rewind and replay it with Disaster Sentinel in place.
- **Phone-screen close-ups** for the SMS alert, like the "+50% IQ" phone shots.
- **End card** with the team logo.

## Shot list

| # | Time | Shot (camera) | What happens | Caption / voiceover | HUD |
|---|------|---------------|--------------|---------------------|-----|
| 1 | 0–3 s | Aerial push-in down a Himalayan valley at dusk | Pine forest, river, small village of houses | **WHAT IF THE MOUNTAINS COULD WARN YOU?** | `UTTARAKHAND` |
| 2 | 3–6 s | Low follow shot by the river | Kid plays by the river, mother calls from the house | "This village sleeps beside the river." | `2:14 AM` |
| 3 | 6–9 s | Wide, looking up the slope | Dark clouds roll in, heavy rain starts | "Then a cloudburst hits." | |
| 4 | 9–12 s | Ground level, water rushing at camera | River overflows and floods the street, a cart floats away | "In minutes, the river becomes a flood." | `WARNING TIME 0 min` (red) |
| 5 | 12–15 s | Orbit around the hillside forest | A spark, then the fire spreads through the pines with smoke | "Up the hill, a spark becomes a wildfire." | |
| 6 | 15–18 s | Side view of the slope | Rain-soaked slope cracks and rocks slide | "Soaked slopes give way." | |
| 7 | 18–21 s | Close-up of a grandmother's phone | Blank screen, no message | "Nobody got a warning." | |
| 8 | 21–23 s | Everything plays backwards with a VHS-style blur | Water and fire pull back | **◀◀ REWIND** | `WARNING TIME ?` |
| 9 | 23–27 s | Crane up past a pole | Our 4 solar nodes pop onto poles (overshoot and settle), with labels FLD1 · SLD2 · FIR3 · POL4 | "Meet Disaster Sentinel." | |
| 10 | 27–30 s | Macro on the flood node (our real enclosure model) | Ultrasonic pulse rings hit the water; a callout reads *Water 2.1 m → 0.9 m* | "Solar sensor nodes watch every river…" | |
| 11 | 30–33 s | Quick cuts: fire node / landslide node | Smoke and flame icon light up; the tilt needle moves | "…every forest, every slope." | |
| 12 | 33–37 s | Aerial: radio rings fly from the nodes across the ridges to the relief centre | Glowing LoRa arcs | "No internet needed. They talk by LoRa radio." | |
| 13 | 37–42 s | Inside the relief centre: push into the Jetson box | A glowing AI brain; a GRU forecast graph draws T+15 / T+30 / T+60 | "The AI reads every signal and predicts the flood an hour before it comes." | `FLOOD RISK T+60: 87%` |
| 14 | 42–45 s | Phone close-up, then the village street | SMS: *⚠ FLOOD ALERT — move to higher ground now.* The siren pole strobes. | "Every phone gets the alert. Sirens sound." | `WARNING TIME 60 min` (green) |
| 15 | 45–49 s | Follow shot up the hill path | Families walk up to the safe shelter; a fire crew truck drives to the forest | "Families reach high ground. Fire crews move early." | `PEOPLE SAFE` counts up |
| 16 | 49–54 s | Wide from the hill | The flood arrives at an empty village; people watch safe from the hill | "When the water comes, no one is there." | `PEOPLE SAFE 1,240` |
| 17 | 54–57 s | Big pull-back aerial | Every node glows and network lines connect them | "Disaster Sentinel. The mountains now have a voice." | |
| 18 | 57–60 s | End card | Logo and project title | **DISASTER SENTINEL** · TEAM WAYWOT · SIH 2026 | |

## Assets (all downloaded, none modelled by hand)
| Need | Source | License |
|------|--------|---------|
| People (kid, mother, grandmother, villagers, fire crew), rigged with walk, run, idle and wave animations | Quaternius *Ultimate Animated Character Pack* / *Universal Animation Library* | CC0 |
| Pine trees, rocks, grass, bushes | Quaternius *Stylized Nature MegaKit* / Kenney *Nature Kit* | CC0 |
| Village houses, cart, fire truck | Kenney *City Kit* / *Car Kit*, Quaternius *Medieval Village* | CC0 |
| Sky / lighting | Poly Haven HDRIs | CC0 |
| Mountains | Blender's bundled terrain generator (A.N.T. Landscape) or a real Uttarakhand height map | — |
| Sensor nodes | **Our own** `hardware/enclosures/stl/` | ours |
| Dashboard on screens | **Our own** `project_images/dashboard_*.png` | ours |
| Sound effects | Freesound / Pixabay (CC0) | CC0 |
