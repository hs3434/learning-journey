# Day 2：原型链、this 绑定、class

## 今日目标
理解 JavaScript 原型继承、this 的四种绑定方式、class 语法

## 学习资料

### 英文（主要）
- [MDN: Prototype](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Inheritance_and_the_prototype_chain)
- [MDN: this](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/this)
- [MDN: Classes](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes)

### 中文（辅助）
- [JavaScript 原型链详解](https://juejin.cn/post/6844903430770180110)
- [this 绑定详解](https://juejin.cn/post/6844903481229679623)

## 理论学习（1小时）

### 原型链
```javascript
// 每个对象都有 prototype
const obj = { a: 1 };
console.log(obj.__proto__ === Object.prototype); // true

// 原型链查找
const parent = { grand: 'grand' };
const child = Object.create(parent);
child.own = 'child';

console.log(child.own);     // 'child' (自有属性)
console.log(child.grand);  // 'grand' (沿原型链查找)

// 构造函数
function Person(name) {
  this.name = name;
}

Person.prototype.greet = function() {
  return `Hello, I'm ${this.name}`;
};

const alice = new Person('Alice');
console.log(alice.greet()); // "Hello, I'm Alice"
console.log(alice.__proto__ === Person.prototype); // true
```

### this 的四种绑定
```javascript
// 1. 默认绑定（严格模式下为 undefined）
function show() {
  console.log(this);
}
show(); // globalThis (浏览器中为 window)

// 2. 隐式绑定
const obj = { name: 'obj', show() { console.log(this.name); } };
obj.show(); // 'obj'，this 指向 obj

// 3. 显式绑定
function greet(greeting) {
  console.log(`${greeting}, ${this.name}`);
}
const person = { name: 'Alice' };
greet.call(person, 'Hi');     // 'Hi, Alice'
greet.apply(person, ['Hi']);  // 'Hi, Alice'
const boundGreet = greet.bind(person, 'Hi');
boundGreet();                  // 'Hi, Alice'

// 4. new 绑定
function Person(name) {
  this.name = name;
}
const p = new Person('Bob'); // this 指向新对象
```

### class 语法
```javascript
class Animal {
  constructor(name) {
    this.name = name;
  }

  speak() {
    return `${this.name} makes a sound`;
  }
}

class Dog extends Animal {
  constructor(name, breed) {
    super(name);
    this.breed = breed;
  }

  speak() {
    return `${this.name} barks`;
  }
}

const dog = new Dog('Rex', 'Shepherd');
console.log(dog.speak()); // 'Rex barks'
console.log(dog instanceof Dog);    // true
console.log(dog instanceof Animal); // true
```

## 练手项目（1.5小时）

### 项目：Week0 JS 基础 - 原型与 class 练习

**需求**：

```javascript
// 1. 原型链继承
function Animal(name) {
  this.name = name;
}

Animal.prototype.speak = function() {
  return `${this.name} makes a sound`;
};

function Dog(name, breed) {
  Animal.call(this, name); // 调用父构造函数
  this.breed = breed;
}

// 设置原型
Dog.prototype = Object.create(Animal.prototype);
Dog.prototype.constructor = Dog;

Dog.prototype.speak = function() {
  return `${this.name} barks`;
};

// 2. class 版本
class Animal {
  constructor(name) {
    this.name = name;
  }
  speak() { return `${this.name} makes a sound`; }
}

class Cat extends Animal {
  constructor(name, color) {
    super(name);
    this.color = color;
  }
  speak() { return `${this.name} meows`; }
}

// 3. this 绑定问题
const person = {
  name: 'Alice',
  // 箭头函数：this 继承外层
  delayedGreet: () => {
    console.log(`Hello, ${this.name}`); // this 不指向 person
  },
  // 普通函数：需要 bind 或箭头函数包装
  greet: function() {
    console.log(`Hello, ${this.name}`);
  }
};
```

**Scaffolding**：

```javascript
// projects/week-00-js-reinforcement/src/prototype.js

// 练习 1：原型链继承
function Vehicle(type) {
  this.type = type;
}
Vehicle.prototype.describe = function() {
  return `A ${this.type}`;
};

function Car(type, brand) {
  // TODO: 调用父构造函数
  // TODO: 设置属性
}

// TODO: 设置 Car.prototype 原型

Car.prototype.drive = function() {
  return `${this.brand} car is driving`;
};

// 练习 2：class 重写
class Vehicle2 {
  // TODO: constructor, describe
}

class Car2 extends Vehicle2 {
  // TODO: constructor, brand, drive
}
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-00-js-reinforcement
node src/prototype.js
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 理解原型链查找机制
- [ ] 理解 this 四种绑定
- [ ] 实现原型链继承
- [ ] 用 class 重写
- [ ] 无运行错误
