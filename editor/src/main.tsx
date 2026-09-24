import { createRoot } from 'react-dom/client';
import '@chirpcoop/real-chicken-ui/styles.css';
import './cap-editor/cap-preview.css';
import './cap-editor/cap-editor.css';
import './demo.css';

import { Page } from './page.js';

createRoot(document.getElementById('root')!).render(<Page />);
