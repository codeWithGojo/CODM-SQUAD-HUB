import { integer, primaryKey, sqliteTable, text } from "drizzle-orm/sqlite-core";

// Each signed-in organizer has independent records for every game.
export const workspaces = sqliteTable("workspaces", {
  owner: text("owner").notNull(),
  game: text("game").notNull(),
  body: text("body").notNull(),
  version: integer("version").notNull().default(1),
  updatedAt: text("updated_at").notNull(),
}, table => [primaryKey({ columns: [table.owner, table.game] })]);
