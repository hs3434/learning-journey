// 异步操作练习
// 运行：node src/async.js

// 练习 1：delay 和 fetchUser
export function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function fetchUser(id) {
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

// 练习 2：async/await
export async function getUserData(id) {
  await delay(100);
  const user = await fetchUser(id);
  const extra = await fetchUser(id + 1);
  return { user, extra };
}

// 练习 3：错误处理
export async function safeGetUserData(id) {
  try {
    return await getUserData(id);
  } catch (error) {
    console.error('Error:', error.message);
    return { user: null, error: error.message };
  }
}

// 练习 4：Promise.all 并行
export async function fetchMultiple(ids) {
  const promises = ids.map(id => fetchUser(id));
  const users = await Promise.all(promises);
  return users;
}

// 测试
async function test() {
  console.log('=== 异步练习 ===');

  console.log('Fetching user 1...');
  const user = await fetchUser(1);
  console.log('User:', user);

  console.log('\nFetching multiple...');
  const users = await fetchMultiple([1, 2, 3]);
  console.log('Users:', users);

  console.log('\nSafe get user -1...');
  const safe = await safeGetUserData(-1);
  console.log('Result:', safe);

  console.log('\nSafe get user 5...');
  const safe2 = await safeGetUserData(5);
  console.log('Result:', safe2);
}

test().catch(console.error);
