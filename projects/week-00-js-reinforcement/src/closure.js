// 闭包练习
// 运行：node src/closure.js

// 练习 1：私有变量
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

// 练习 2：工厂函数
function createMultiplier(factor) {
  return function(number) {
    return number * factor;
  };
}

// 练习 3：闭包问题修复
function createFunctions() {
  const functions = [];
  for (var i = 0; i < 3; i++) {
    functions.push(function() { return i; });
  }
  return functions;
}

function createFunctionsFixed() {
  const functions = [];
  for (let i = 0; i < 3; i++) {
    functions.push((function(captured) {
      return function() { return captured; };
    })(i));
  }
  return functions;
}

// 测试
console.log('=== 闭包练习 ===');
const account = createBankAccount(100);
console.log('Balance:', account.getBalance());
console.log('After deposit:', account.deposit(50));
console.log('After withdraw:', account.withdraw(30));

const double = createMultiplier(2);
const triple = createMultiplier(3);
console.log('double(5):', double(5));
console.log('triple(5):', triple(5));

const funcs = createFunctions();
console.log('createFunctions (broken):', funcs.map(f => f())); // [3,3,3]

const funcsFixed = createFunctionsFixed();
console.log('createFunctionsFixed:', funcsFixed.map(f => f())); // [0,1,2]
