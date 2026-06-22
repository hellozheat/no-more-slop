const groups = Object.keys(items).reduce((acc, key) => {
  const k = items[key].category;
  if (!acc[k]) acc[k] = [];
  acc[k].push(items[key]);
  return acc;
}, {} as Record<string, typeof items[string][]>);
