CREATE TABLE `organizer_accounts` (
	`id` text PRIMARY KEY NOT NULL,
	`email` text NOT NULL,
	`password_hash` text NOT NULL,
	`display_name` text NOT NULL,
	`created_at` text NOT NULL
);
CREATE UNIQUE INDEX `organizer_accounts_email_unique` ON `organizer_accounts` (`email`);
