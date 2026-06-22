function activeUsers(users) {
  return users.filter((u) => u.isActive);
}

export { activeUsers };
