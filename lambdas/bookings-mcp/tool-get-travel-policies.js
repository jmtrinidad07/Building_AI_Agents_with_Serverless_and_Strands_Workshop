import log4js from 'log4js';
import { logToolExecution } from './logging.js';

const l = log4js.getLogger();

const TOOL = [
  "get-travel-policies",
  "This tool returns corporate travel policies. Travel agents must ALWAYS follow this guidance and restrictions.",
  async (ctx) => {
    const startTime = Date.now();
    const userId = ctx.authInfo.user_id;
    const userName = ctx.authInfo.user_name;
    
    l.info(`TOOL_START: get-travel-policies for user_id=${userId}, user_name=${userName}`);
    
    try {
      const policies = `Here are the travel policies for ${userName}:
1. Employees can only book travel within the United States of America.
2. Employees are not allowed to book luxury cars.
3. Employees cannot travel for more than 5 days.
4. Employees can book business travel only, no leisure or personal travel is supported.`;

      const result = {
        content: [
          {
            type: "text",
            text: policies
          }
        ]
      };
      
      const endTime = Date.now();
      logToolExecution('get-travel-policies', userId, startTime, endTime, true);
      
      l.info(`TOOL_RESULT: get-travel-policies returned ${policies.length} characters of policy data`);
      
      return result;
      
    } catch (error) {
      const endTime = Date.now();
      logToolExecution('get-travel-policies', userId, startTime, endTime, false, error.message);
      throw error;
    }
  }
];

export default TOOL;
