import log4js from 'log4js';
import { z } from 'zod';
import { logToolExecution } from './logging.js';

const l = log4js.getLogger();

const WEATHER_DATA = {
  'New York': { temp: '22°C', condition: 'Partly cloudy', humidity: '65%' },
  'Paris': { temp: '18°C', condition: 'Light rain', humidity: '80%' },
  'London': { temp: '15°C', condition: 'Overcast', humidity: '75%' },
  'Tokyo': { temp: '25°C', condition: 'Sunny', humidity: '60%' },
  'Seattle': { temp: '16°C', condition: 'Rainy', humidity: '85%' },
  'Dallas': { temp: '28°C', condition: 'Hot and sunny', humidity: '45%' }
};

const RECOMMENDATIONS = {
  'Light rain': 'Pack an umbrella and waterproof jacket',
  'Rainy': 'Bring rain gear and waterproof shoes',
  'Sunny': 'Don\'t forget sunscreen and sunglasses',
  'Hot and sunny': 'Stay hydrated and wear light clothing',
  'Overcast': 'Layer clothing for variable temperatures',
  'Partly cloudy': 'Perfect weather for outdoor activities'
};

const TOOL = [
  "get-weather",
  "Get current weather information for a travel destination",
  {
    city: z.string(),
    country: z.string().optional()
  },
  async ({ city, country }, ctx) => {
    const startTime = Date.now();
    const userId = ctx.authInfo.user_id;
    const userName = ctx.authInfo.user_name;
    
    l.info(`TOOL_START: get-weather of user_id=${userId}, user_name=${userName}`);
    l.info(`WEATHER_PARAMS: city=${city}, country=${country || 'not specified'}`);
    
    try {
      const location = country ? `${city}, ${country}` : city;
      const weather = WEATHER_DATA[city] || {
        temp: '20°C',
        condition: 'Variable conditions',
        humidity: '70%'
      };
      
      const recommendation = RECOMMENDATIONS[weather.condition] || 'Check local weather before departure';
      
      const weatherReport = `Weather for ${location}:
Temperature: ${weather.temp}
Condition: ${weather.condition}
Humidity: ${weather.humidity}
Travel Tip: ${recommendation}`;

      const result = {
        content: [
          {
            type: "text",
            text: weatherReport
          }
        ]
      };
      
      const endTime = Date.now();
      logToolExecution('get-weather', userId, startTime, endTime, true);
      
      l.info(`WEATHER_SUCCESS: Weather data provided for ${location}`);
      
      return result;
      
    } catch (error) {
      const endTime = Date.now();
      logToolExecution('get-weather', userId, startTime, endTime, false, error.message);
      l.error(`WEATHER_FAILED: ${error.message}`);
      throw error;
    }
  }
];

export default TOOL;