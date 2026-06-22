import { groupBy } from "lodash-es";

const groups = groupBy(Object.values(items), "category");
