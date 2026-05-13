// 原型链和 class 练习
// 运行：node src/prototype.js

// 练习 1：原型链继承
function Vehicle(type) {
  this.type = type;
}

Vehicle.prototype.describe = function() {
  return `A ${this.type}`;
};

function Car(type, brand) {
  Vehicle.call(this, type);
  this.brand = brand;
}

Car.prototype = Object.create(Vehicle.prototype);
Car.prototype.constructor = Car;

Car.prototype.drive = function() {
  return `${this.brand} car is driving`;
};

// 练习 2：class 版本
class Vehicle2 {
  constructor(type) {
    this.type = type;
  }

  describe() {
    return `A ${this.type}`;
  }
}

class Car2 extends Vehicle2 {
  constructor(type, brand) {
    super(type);
    this.brand = brand;
  }

  drive() {
    return `${this.brand} car is driving`;
  }
}

// 测试
console.log('=== 原型链练习 ===');
const vehicle = new Vehicle('car');
console.log(vehicle.describe());

const car = new Car('automobile', 'Toyota');
console.log(car.describe());
console.log(car.drive());

console.log('\n=== Class 练习 ===');
const vehicle2 = new Vehicle2('car');
console.log(vehicle2.describe());

const car2 = new Car2('automobile', 'Honda');
console.log(car2.describe());
console.log(car2.drive());
