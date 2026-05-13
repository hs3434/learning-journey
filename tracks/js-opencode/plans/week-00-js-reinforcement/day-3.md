# Day 3：Promise、async/await、错误处理

## 今日目标
掌握 Promise 用法、async/await 语法、错误捕获模式

## 学习资料

### 英文（主要）
- [MDN: Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)
- [MDN: async function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)
- [MDN: try...catch](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/try...catch)

### 中文（辅助）
- [Promise 详解](https://juejin.cn/post/6844903607294804995)
- [async/await 详解](https://juejin.cn/post/6844903607508214791)

## 理论学习（1小时）

### Promise 基础
```javascript
// 创建 Promise
const promise = new Promise((resolve, reject) => {
  setTimeout(() => {
    resolve('success');
    // 或 reject(new Error('failed'));
  }, 1000);
});

// 使用 then/catch
promise
  .then(result => console.log(result))
  .catch(error => console.error(error));

// Promise 链
fetch('/api/user')
  .then(res => res.json())
  .then(user => fetch(`/api/posts/${user.id}`))
  .then(res => res.json())
  .then(posts => console.log(posts))
  .catch(error => console.error(error));
```

### async/await
```javascript
// async 函数返回 Promise
async function fetchUser() {
  const res = await fetch('/api/user');
  const user = await res.json();
  return user;
}

// 错误处理：try/catch
async function safeFetchUser() {
  try {
    const res = await fetch('/api/user');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (error) {
    console.error('Failed to fetch user:', error);
    return null;
  }
}

// 多个异步操作
async function fetchAll() {
  // 串行：逐个等待
  const user = await fetchUser();
  const posts = await fetchPosts();

  // 并行：同时发起（推荐）
  const [user, posts] = await Promise.all([
    fetchUser(),
    fetchPosts()
  ]);

  // Promise.allSettled：不怕部分失败
  const results = await Promise.allSettled([
    fetchUser(),
    fetchPosts()
  ]);
}
```

### 错误类型
```javascript
// 抛出错误
throw new Error('something wrong');

// 捕获错误
try {
  riskyOperation();
} catch (error) {
  if (error instanceof TypeError) {
    console.error('Type error:', error.message);
  } else if (error instanceof ReferenceError) {
    console.error('Reference error:', error.message);
  } else {
    console.error('Unknown error:', error);
  }
}
```

## 练手项目（1.5小时）

### 项目：Week0 JS 基础 - 异步操作练习

**需求**：

```javascript
// 1. Promise 实现
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function fetchUser(id) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (id > 0) {
        resolve({ id, name: `User ${id}` });
      } else {
        reject(new Error('Invalid user id'));
      }
    }, 100);
  });
}

// 2. async/await 重写
async function getUserData(id) {
  await delay(100);
  const user = await fetchUser(id);
  const extra = await fetchUser(id + 1);
  return { user, extra };
}

// 3. 错误处理
async function safeGetUserData(id) {
  try {
    return await getUserData(id);
  } catch (error) {
    console.error('Error:', error.message);
    return { user: null, error: error.message };
  }
}

// 4. Promise.all 并行
async function fetchMultiple(ids) {
  const promises = ids.map(id => fetchUser(id));
  const users = await Promise.all(promises);
  return users;
}
```

**Scaffolding**：

```javascript
// projects/week-00-js-reinforcement/src/async.js

export function delay(ms) {
  // TODO: 返回 Promise，ms 毫秒后 resolve
}

export function fetchUser(id) {
  // TODO: 返回 Promise，id > 0 时 resolve user，否则 reject Error
}

export async function getUserData(id) {
  // TODO: 用 async/await 实现
}

export async function safeGetUserData(id) {
  // TODO: try/catch 错误处理
}

export async function fetchMultiple(ids) {
  // TODO: Promise.all 并行获取
}
```

## 调试复盘（0.5小时）

### 验证方式
```bash
cd projects/week-00-js-reinforcement
node src/async.js
```

### 今日问题记录
```
1.
2.
3.
```

## 产出检查清单
- [ ] 实现 delay 和 fetchUser Promise
- [ ] 用 async/await 重写
- [ ] 实现 safeGetUserData 错误处理
- [ ] 实现 fetchMultiple 并行
- [ ] 无运行错误
