# Plinko
Plinko game generated using chatgpt


## Requirements for the plinko game  in pygame given to chatgpt
1. The player will start with 1000 points
2. Create a slider that the player can use to wager their points
    * The player has to wager at least 1 point.
    * The player can wager all of their points if they wish
    * Also have a text input field to assist in editing the wager
3. Create another slider that controls the number of rows of pegs the board contains.
    * The board must have between 5 and 20 rows
    * The number of pegs per row is n + 1 pegs. So first row will have 2 pegs.
    * The shape of the board will be a triangle
4. Create a button that the player has to press to drop a ball into the plinko.
    * The wager should be subtracted from the players total points
    * The ball should be dropped randomly between the first two pegs.
4. The ball will always be dropped randomly between the first two pegs.
5. Place little square buckets the ball can drop into at the end of the board.
    * Each bucket will have a multiplier. Have the multipliers be lower than 1x in the middle.
    * have the multipliers increase towards the outside buckets.
    * The multipliers should increase with the number of rows.
    * Add the multiplier times the wager to the players points.
    * Delete the ball from the screen
6. Create a new difficulty slider.
    * Increased difficulty causes the middle multipliers to go down and the outter multipliers to go up.