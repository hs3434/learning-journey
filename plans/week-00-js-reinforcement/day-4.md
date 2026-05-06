# Day 4：事件循环、微任务与宏任务

## 今日目标
理解 JavaScript 事件循环机制、微任务队列、宏任务队列

## 学习资料

### 英文（主要）
- [Node.js Event Loop](https://nodejs.org/en/guides/event-loop-timers-and-nexttick)
- [Jake Archibald: Tasks, microtasks](https://jakearchibald.com/2015/tasks-microtasks-queues-and-schedules/)

### 中文（辅助）
- [JavaScript 事件循环详解](https://juejin.cn/post/6844903950554603534)

## 理论学习（1小时）

### 事件循环概念
```
┌───────────────────────┐
│        call stack     │  执行同步代码
└───────────────────────┘
           ↓
┌───────────────────────┐
│     microtasks queue  │  Promise.then, queueMicrotask
└───────────────────────┘
           ↓
┌───────────────────────┐
│      macrotasks queue │  setTimeout, setInterval, I/O
└───────────────────────┘
```

### 执行顺序
```javascript
console.log('1');

setTimeout(() => console.log('2'), 0);

Promise.resolve().then(() => console.log('3'));

console.log('4');

// 输出：1, 4, 3, 2
// 原因：
// 1. console.log('1') - 同步，直接执行
// 2. setTimeout - 宏任务，排队
// 3. Promise.then - 微任务，排队
// 4. console.log('4') - 同步，直接执行
// 5. 清空微任务队列
// 6. 清空一个宏任务
```

### 深入理解
```javascript
console.log('script start');

setTimeout(() => console.log('setTimeout'), 0);

Promise.resolve()
  .then(() => console.log('promise1'))
  .then(() => console.log('promise2'));

Promise.resolve().then(() => {
  console.log('promise3');
  setTimeout(() => console.log('setTimeout in promise'), 0);
});

console.log('script end');

// 输出顺序：
// script start
// script end
// promise1
// promise3
// promise2
// setTimeout        (第一个 setTimeout)
// setTimeout in promise  (第二个 setTimeout)
```

### process.nextTick vs setImmediate
```javascript
// Node.js 特有
process.nextTick(() => console.log('nextTick'));
setImmediate(() => console.log('setImmediate'));

// nextTick 比 setImmediate 优先级高
// 因为 nextTick 在当前执行阶段结束后立即执行
// 而 setImmediate 在下一个事件循环阶段执行
```

## 练手项目（1.5小时）

### 项目：Week0 JS 基础 - 事件循环练习

**需求**：

```javascript
// 1. 预测输出
function predictOutput() {
  console.log('A');

  setTimeout(() => console.log('B'), 0);

  Promise.resolve().then(() => console.log('C'));

  console.log('D');
}

// 答案应该是：A, D, C, B

// 2. 进阶：嵌套
console.log('1');

setTimeout(() => {
  console.log('2');

  Promise.resolve().then(() => {
    console.log('3');
  });
}, 0);

Promise.resolve().then(() => console.log('4'));

setTimeout(() => console.log('5'), 0);

console.log('6');

// 答案：1, 6, 4, 2, 3, 5

// 3. async/await 中的微任务
async function test() {
  console.log('start');

  await Promise.resolve();
  console.log('after await');  // 这行在微任务中

  setTimeout(() => console.log('timeout'), 0);

  await Promise.resolve();
  console.log('after second await');  // 这行也在微任务中

  console.log('end');
}

test();
console.log('sync code');

// 输出：start, sync code, after await, after second await, end, timeout
```

**验证方式**：

```javascript
// projects/week-00-js-reinforcement/src/event-loop.js

// 练习：运行并验证输出
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

// 依次运行
exercise1();
setTimeout(() => {
  exercise2();
  setTimeout(() => exercise3(), 100);
}, 50);
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-00-js-reinforcement
node src/event-loop.js
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 理解事件循环机制
- [ ] 区分微任务和宏任务
- [ ] 能预测简单代码输出
- [ ] 理解 async/await 中的微任务
- [ ] 无运行错误
