import { z } from 'zod';
import log4js from 'log4js';
import { logToolExecution } from './logging.js';

const l = log4js.getLogger();

const CARS = [
  "Toyota Corolla",
  "Honda CRV", 
  "Mercedes C300"
];

const CATEGORIES = {
  0: "sedan",
  1: "suv", 
  2: "luxury"
};

const TOOL = [
  "book-car",
  "Use this tool to book car rentals. Supported categories: 0-sedan, 1-suv, 2-luxury",
  {
    city: z.string(),
    date: z.string(),
    days: z.number(),
    category: z.number().optional()
  },
  async ({ city, date, days, category }, ctx) => {
    const startTime = Date.now();
    const userId = ctx.authInfo.user_id;
    const userName = ctx.authInfo.user_name;
    
    l.info(`TOOL_START: book-car for user_id=${userId}, user_name=${userName}`);
    l.info(`BOOKING_PARAMS: city=${city}, date=${date}, days=${days}, category=${category}`);
    
    try {
      // Validate category
      const carCategory = category || 0;
      if (carCategory < 0 || carCategory >= CARS.length) {
        throw new Error(`Invalid car category: ${carCategory}. Must be 0-${CARS.length-1}`);
      }
      
      const car = CARS[carCategory];
      const categoryName = CATEGORIES[carCategory];
      
      l.info(`CAR_SELECTED: ${car} (${categoryName}) for ${days} days`);
      
      // Simulate booking validation
      if (days > 30) {
        throw new Error(`Booking period too long: ${days} days. Maximum is 30 days.`);
      }
      
      const bookingResult = `Booked a ${car} for ${userName} in ${city} for ${days} days starting ${date}`;
      
      const result = {
        content: [
          {
            type: "text",
            text: bookingResult
          }
        ]
      };
      
      const endTime = Date.now();
      logToolExecution('book-car', userId, startTime, endTime, true);
      
      l.info(`BOOKING_SUCCESS: ${car} booked for ${userName} in ${city}`);
      
      return result;
      
    } catch (error) {
      const endTime = Date.now();
      logToolExecution('book-car', userId, startTime, endTime, false, error.message);
      l.error(`BOOKING_FAILED: ${error.message}`);
      throw error;
    }
  }
];

export default TOOL;
