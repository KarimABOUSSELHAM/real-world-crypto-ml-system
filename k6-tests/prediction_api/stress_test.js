import http from 'k6/http'; 
import { sleep } from 'k6';

export const options = {
    stages: [
        { duration: '5m', target: 200 }, // ramp up to 200 VUs over 5 minutes
        { duration: '15m', target: 200 }, // stay at 200 VUs for 15 minutes
        { duration: '5m', target: 0 },    // ramp down to 0 users
    ],
};

export default function () {
    const url = 'http://127.0.0.1:3001/prediction?pair=ETH/EUR'; // For the python prediction
    // API I used the port 8000
    const res = http.get(url);

  sleep(1); // pause for 1 second before next iteration
}