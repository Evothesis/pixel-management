import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Setup the mock server with our handlers
export const server = setupServer(...handlers);