CREATE TABLE `workspaces` (
	`owner` text NOT NULL,
	`game` text NOT NULL,
	`body` text NOT NULL,
	`version` integer DEFAULT 1 NOT NULL,
	`updated_at` text NOT NULL,
	PRIMARY KEY(`owner`, `game`)
);
