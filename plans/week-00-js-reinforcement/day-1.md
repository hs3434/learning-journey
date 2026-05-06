# Day 1：变量、函数、作用域、闭包

## 今日目标
理解 JavaScript 变量声明（var/let/const）、函数定义、作用域规则、闭包原理

## 学习资料

### 英文（主要）
- [MDN: var, let, const](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements)
- [MDN: Closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Closures)
- [MDN: Functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions)

### 中文（辅助）
- [JavaScript 闭包详解](https://juejin.cn/post/6844903468132098061)
- [var let const 区别](https://juejin.cn/post/6844903974372110349)

## 理论学习（1小时）

### 变量声明
```javascript
// var：函数作用域，可重复声明（不推荐）
var x = 1;
var x = 2; // 允许

// let：块级作用域，不可重复声明
let y = 1;
let y = 2; // SyntaxError

// const：块级作用域，必须初始化，不能重新赋值
const z = 1;
z = 2; // TypeError

// const 对象：可以修改属性
const obj = { a: 1 };
obj.a = 2; // OK
obj = {}; // TypeError
```

### 函数定义
```javascript
// 函数声明（hoisted）
function sum(a, b) {
  return a + b;
}

// 函数表达式
const sum = function(a, b) {
  return a + b;
};

// 箭头函数
const sum = (a, b) => a + b;
const sum = (a, b) => { return a + b; };
```

### 作用域
```javascript
// 全局作用域
const globalVar = 1;

function outer() {
  // outer 作用域
  const outerVar = 2;

  function inner() {
    // inner 作用域
    const innerVar = 3;
    console.log(globalVar); // 1
    console.log(outerVar);  // 2
    console.log(innerVar);  // 3
  }

  inner();
  // console.log(innerVar); // ReferenceError
}
```

### 闭包
```javascript
// 闭包：函数能记住并访问其词法作用域
function createCounter() {
  let count = 0;  // 私有变量

  return function() {
    count++;
    return count;
  };
}

const counter = createCounter();
console.log(counter()); // 1
console.log(counter()); // 2
console.log(counter()); // 3
// count 被隐藏，但持续存在
```

## 练手项目（1.5小时）

### 项目：Week0 JS 基础 - 函数与闭包练习

**需求**：

```javascript
// 1. 闭包实现私有变量
function createBankAccount(initialBalance) {
  let balance = initialBalance;

  return {
    deposit: function(amount) {
      if (amount <= 0) throw new Error('Amount must be positive');
      balance += amount;
      return balance;
    },
    withdraw: function(amount) {
      if (amount > balance) throw new Error('Insufficient funds');
      balance -= amount;
      return balance;
    },
    getBalance: function() {
      return balance;
    }
  };
}

// 2. 闭包实现工厂函数
function createMultiplier(factor) {
  return function(number) {
    return number * factor;
  };
}

const double = createMultiplier(2);
const triple = createMultiplier(3);

// 3. 循环中的闭包问题
function createFunctions() {
  const functions = [];

  for (var i = 0; i < 3; i++) {
    functions.push(function() {
      return i;  // 问题：所有函数都返回 3
    });
  }

  return functions;
}

// 修复：用 let 或闭包保存变量
function createFunctionsFixed() {
  const functions = [];

  for (let i = 0; i < 3; i++) {
    functions.push((function(captured) {
      return function() { return captured; };
    })(i));
  }

  return functions;
}
```

**Scaffolding**：

```javascript
// projects/week-00-js-reinforcement/src/closure.js

// 练习 1：私有变量
function createBankAccount(initialBalance) {
  // TODO: 实现
}

// 练习 2：工厂函数
function createMultiplier(factor) {
  // TODO: 返回乘以 factor 的函数
}

// 练习 3：修复闭包问题
function createFunctions() {
  const functions = [];
  for (var i = 0; i < 3; i++) {
    functions.push(function() { return i; });
  }
  return functions;
}
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-00-js-reinforcement
node src/closure.js
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 理解 var/let/const 区别
- [ ] 理解函数作用域
- [ ] 理解闭包原理
- [ ] 实现私有变量闭包
- [ ] 无运行错误
