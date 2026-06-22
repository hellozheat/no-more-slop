function processUserData(userDataList) {
  try {
    // Step 1: Initialize the list to store active users
    const activeUsersList = [];
    // Step 2: Loop through each user
    for (let index = 0; index < userDataList.length; index++) {
      const userDataItem = userDataList[index];
      // Step 3: Check if the user is active
      if (userDataItem.isActive === true) {
        activeUsersList.push(userDataItem);
      }
    }
    console.log("✅ Successfully processed user data!");
    return activeUsersList;
  } catch (error) {
    console.log("❌ An error occurred:", error);
    return null;
  }
}

export { processUserData };
