const AUTH_MESSAGES: Record<string, string> = {
	INVALID_CREDENTIALS: 'Email or password is incorrect.',
	EMAIL_ALREADY_REGISTERED: 'An account with this email already exists.',
	EMAIL_ALREADY_EXISTS: 'An account with this email already exists.',
	REGISTER_USER_ALREADY_EXISTS: 'An account with this email already exists.',
	INVALID_PASSWORD: 'Choose a stronger password and try again.',
	CURRENT_PASSWORD_INVALID: 'The current password is incorrect.',
	DEMO_ACCOUNT_UNAVAILABLE: 'The demo account is temporarily unavailable. Please try again.',
	VALIDATION_ERROR: 'Check the information you entered and try again.',
	AUTH_REQUEST_FAILED: 'Authentication could not be completed. Please try again.'
};

export function authMessage(code: string | undefined): string {
	return AUTH_MESSAGES[code ?? 'AUTH_REQUEST_FAILED'] ?? AUTH_MESSAGES.AUTH_REQUEST_FAILED;
}
