// 事件循环练习
// 运行：node src/event-loop.js

console.log('=== 事件循环练习 ===');

function exercise1() {
  console.log('A');
  setTimeout(() => console.log('B'), 0);
  Promise.resolve().then(() => console.log('C'));
  console.log('D');
}

function exercise2() {
  console.log('1');
  setTimeout(() => {
    console.log('2');
    Promise.resolve().then(() => console.log('3'));
  }, 0);
  Promise.resolve().then(() => console.log('4'));
  setTimeout(() => console.log('5'), 0);
  console.log('6');
}

async function exercise3() {
  console.log('start');
  await Promise.resolve();
  console.log('after await');
  setTimeout(() => console.log('timeout'), 0);
  await Promise.resolve();
  console.log('after second await');
  console.log('end');
}

console.log('\n--- Exercise 1 ---');
exercise1();
console.log('Expected: A, D, C, B');

setTimeout(() => {
  console.log('\n--- Exercise 2 ---');
  exercise2();
  console.log('Expected: 1, 6, 4, 2, 3, 5');

  setTimeout(() => {
    console.log('\n--- Exercise 3 ---');
    exercise3();
    console.log('Expected: start, (sync), after await, after second await, end, timeout');
  }, 100);
}, 100);
