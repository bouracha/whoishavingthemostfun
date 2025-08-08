# Frontend Manual Testing Checklist

Use this checklist to manually verify frontend functionality across different browsers and devices.

## Prerequisites
- [ ] Flask server is running (`python server.py`)
- [ ] Access via `http://localhost:8080` (not file:// URLs)
- [ ] Test on multiple browsers: Chrome, Firefox, Safari, Edge
- [ ] Test on mobile device or browser dev tools mobile view

---

## Homepage (`/` or `index.html`)

### Visual Elements
- [ ] Monica Geller quote displays correctly
- [ ] Monica image loads and displays
- [ ] Three game buttons (Chess, Backgammon, Ping Pong) are visible and styled
- [ ] Page layout is responsive on mobile

### Functionality
- [ ] Server status check works (no offline warning when server running)
- [ ] Server offline warning appears when API is unreachable
- [ ] Chess button navigates to `chess.html`
- [ ] Backgammon button navigates to `backgammon.html` 
- [ ] Ping Pong button navigates to `pingpong.html`

### Cross-Browser
- [ ] Chrome: All elements display correctly
- [ ] Firefox: All elements display correctly
- [ ] Safari: All elements display correctly
- [ ] Mobile: Layout adapts properly, buttons are touchable

---

## Chess Page (`chess.html`)

### Visual Elements
- [ ] Chess leaderboard image loads and displays clearly
- [ ] Chess rating progress chart loads and displays
- [ ] "Add Player" button is visible and styled
- [ ] "🏠 Home" button is visible
- [ ] Page title shows chess-related content

### Navigation
- [ ] Home button returns to main page
- [ ] Page loads directly via URL (`/chess.html`)

### Add Player Functionality
- [ ] "Add Player" button opens modal dialog
- [ ] Modal has input field for player name
- [ ] Modal has "Add Player" and "Cancel" buttons
- [ ] "Cancel" closes modal without action
- [ ] "Add Player" with valid name shows success message
- [ ] "Add Player" with empty name shows error
- [ ] Page refreshes after successful player addition
- [ ] New leaderboard/charts reflect added player

### Error Handling
- [ ] Network error shows appropriate message
- [ ] Server offline shows appropriate message
- [ ] Invalid player names handled gracefully

---

## Ping Pong Page (`pingpong.html`)

### Visual Elements
- [ ] Ping pong leaderboard image loads and displays
- [ ] Ping pong rating progress chart loads and displays
- [ ] "Add Player" button is visible and styled
- [ ] "🏠 Home" button is visible

### Functionality (same tests as Chess)
- [ ] Navigation works correctly
- [ ] Add player modal functions properly
- [ ] API calls work for pingpong endpoint
- [ ] Charts update after player addition

---

## Backgammon Page (`backgammon.html`)

### Visual Elements
- [ ] Backgammon leaderboard image loads (or placeholder)
- [ ] Backgammon rating progress chart loads (or placeholder)
- [ ] "Add Player" button is visible and styled
- [ ] "🏠 Home" button is visible

### Functionality (same tests as Chess)
- [ ] Navigation works correctly
- [ ] Add player modal functions properly
- [ ] API calls work for backgammon endpoint
- [ ] Charts update after player addition

---

## Mobile Responsiveness

### Portrait Mode
- [ ] All pages display correctly in portrait orientation
- [ ] Buttons are appropriately sized for touch
- [ ] Text is readable without zooming
- [ ] Images scale appropriately
- [ ] Modals display correctly

### Landscape Mode
- [ ] All pages adapt to landscape orientation
- [ ] No horizontal scrolling required
- [ ] All functionality remains accessible

---

## Performance & Loading

### Image Loading
- [ ] Leaderboard images load within 3 seconds
- [ ] Rating progress charts load within 3 seconds
- [ ] Player photos in leaderboards display correctly
- [ ] Medal icons display correctly
- [ ] No broken image icons

### API Response Times
- [ ] Health check responds within 1 second
- [ ] Add player requests complete within 5 seconds
- [ ] Page refresh after player addition completes within 10 seconds

---

## Accessibility

### Keyboard Navigation
- [ ] Tab navigation works through all interactive elements
- [ ] Enter key activates buttons
- [ ] Escape key closes modals
- [ ] Focus indicators are visible

### Screen Reader Compatibility
- [ ] Images have appropriate alt text
- [ ] Buttons have descriptive labels
- [ ] Form inputs have proper labels
- [ ] Page structure is logical

---

## Error Scenarios

### Network Issues
- [ ] Test with network disconnected - offline warning appears
- [ ] Test with slow network - loading states work
- [ ] Test API server stopped - appropriate error messages

### Invalid Data
- [ ] Test adding player with special characters
- [ ] Test adding very long player names
- [ ] Test adding duplicate player names
- [ ] Test malformed API responses

---

## Browser-Specific Issues

### Chrome
- [ ] No console errors in DevTools
- [ ] CORS requests work properly
- [ ] Local storage (if used) functions correctly

### Firefox
- [ ] No console errors in DevTools
- [ ] All CSS styles render correctly
- [ ] JavaScript functions work as expected

### Safari
- [ ] No console errors in Web Inspector
- [ ] Fetch API calls work properly
- [ ] Mobile Safari touch events work

### Edge
- [ ] No console errors in DevTools
- [ ] All modern JavaScript features work
- [ ] Layout renders consistently

---

## Test Results

**Date:** ___________  
**Tester:** ___________  
**Environment:** ___________

### Issues Found:
1. 
2. 
3. 

### Overall Status:
- [ ] All tests passed - Ready for production
- [ ] Minor issues found - Acceptable for release
- [ ] Major issues found - Needs fixes before release