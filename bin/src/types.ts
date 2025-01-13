export interface Flashcard {
  id: string;
  prompt: string;
  answer: string;
  category: string;
  difficulty: 'easy' | 'medium' | 'hard';
  mastered: boolean;
  folderId: string;
  lastReviewed?: Date;
}

export interface Folder {
  id: string;
  name: string;
  description?: string;
  color?: string;
  createdAt: Date;
}

export interface User {
  isAuthenticated: boolean;
  token: string | null;
}

export interface StudyProgress {
  total: number;
  mastered: number;
  byDifficulty: {
    easy: number;
    medium: number;
    hard: number;
  };
}