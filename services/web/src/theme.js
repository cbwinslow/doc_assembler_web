import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#00FF00', // Matrix green
    },
    secondary: {
      main: '#008000', // Darker green
    },
    background: {
      default: '#000000', // Black background
      paper: '#004000', // Dark green paper
    },
  },
});

export default theme;

