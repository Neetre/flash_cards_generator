export interface Flashcard {
    prompt: string;
    answer: string;
    category: string;
    difficulty: string;
  }
  
  export interface LoginResponse {
    token: string;
  }
  
  export interface User {
    isAuthenticated: boolean;
    token: string | null;
  }