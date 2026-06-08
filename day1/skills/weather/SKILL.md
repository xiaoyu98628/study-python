---
name: weather
description: Use this skill when the user asks about current weather, tomorrow's weather, forecasts, temperature, rain, wind, humidity, visibility, or travel weather.
---

# Weather

## Instructions

When using this skill:

1. If the user does not provide a location and the question depends on the current location, call `get_current_location` first.
2. For current weather, call `get_weather` with `include_forecast=false`.
3. For tomorrow, future weather, or forecast questions, call `get_weather` with `include_forecast=true`.
4. Answer in the user's language and keep weather details practical.
5. If location comes from IP geolocation, mention that it is an approximate network location.

## Tools

- get_weather
- get_current_location
