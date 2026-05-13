// 异步工具函数
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

export async function safeGetUserData(id) {
  try {
    const user = await fetchUser(id);
    return { user, error: null };
  } catch (error) {
    return { user: null, error: error.message };
  }
}
