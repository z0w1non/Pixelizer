source .venv/Scripts/activate
for i in {01..24}; do python main.py "Sample/Input/PhotoCD_PCD0992/${i}.png" "Sample/Output/PhotoCD_PCD0992/${i}.png"; done