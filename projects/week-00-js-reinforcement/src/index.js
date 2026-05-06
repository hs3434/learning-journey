// 模块练习
// 运行：node src/index.js

// 导入模块
import { add, multiply, sum } from './modules/math.js';
import { capitalize, truncate } from './modules/string.js';

console.log('=== 模块练习 ===');
console.log('add(1, 2):', add(1, 2));
console.log('multiply(3, 4):', multiply(3, 4));
console.log('sum(1, 2, 3, 4):', sum(1, 2, 3, 4));
console.log('capitalize("hello"):', capitalize('hello'));
console.log('truncate("Hello World", 5):', truncate('Hello World', 5));

console.log('\n=== 工具函数练习 ===');
import { delay, fetchUser, safeGetUserData } from './utils/async.js';

async function testAsync() {
  console.log('delay 100ms...');
  await delay(100);
  console.log('done');

  console.log('\nfetchUser(1):', await fetchUser(1));
  console.log('safeGetUserData(-1):', await safeGetUserData(-1));
}

testAsync().catch(console.error);
