#include <Arduino.h>
#include "serial_com.h"

bool DEBUG = false;          // Global debug flag
const char *O_CODE = "TEST"; // OpenBIS code for the device
int MAX_LENGTH = 64;         // Maximum allowed length of a message line

/**
 * @brief Initializes the serial communication and sets the debug mode
 *
 * @param debug_on Flag to enable or disable debug output
 */
void init(bool debug_on, const char *openbiscode, int max_length)
{
    DEBUG = debug_on;
    O_CODE = openbiscode;
    MAX_LENGTH = max_length;
}

/**
 * @brief Checks if a string is a valid integer
 *
 * @param str The string to check
 * @return true if the string is a valid integer, false otherwise
 */
bool isInteger(const char *str)
{
    if (str[0] == '-' && strlen(str) > 1)
    {
        str++; // Allow negative numbers, skip the minus sign
    }

    for (int i = 0; str[i] != '\0'; i++)
    {
        if (str[i] < '0' || str[i] > '9')
        {
            return false; // Invalid character
        }
    }
    return true; // Valid number
}

/**
 * @brief Validates a received message according to specific format rules
 *
 * This function checks if the message contains only valid integers separated by commas.
 *
 * @param msg The message to validate
 * @return true if the message is valid, false otherwise
 */
bool validateMessage(volatile char *msg)
{
    int numberCount = 0; // Number of integers found
    char temp[10];       // Buffer for current number
    int tempIndex = 0;   // Index for temporary number
    bool isValid = true;

    if (DEBUG)
    {
        Serial.print("Complete message is ");
        Serial.println((const char *)msg);
    }

    // Parse the message character by character
    for (int i = 0; msg[i] != '\0'; i++)
    {
        char currentChar = msg[i];
        if (DEBUG)
        {
            Serial.print("Character " + String(i) + " is: ");
            Serial.println(currentChar);
        }

        if (currentChar == 0x0D)
        {
            if (DEBUG)
                Serial.println("\t Character is CR (ignored)");
            continue; // Skip CR character
        }

        if ((currentChar >= '0' && currentChar <= '9') || currentChar == '-')
        {
            // Valid digit or minus sign
            if (DEBUG)
                Serial.println("\t Character is between '0' and '9' or '-'");
            temp[tempIndex++] = currentChar;
        }
        else if (currentChar == ',')
        {
            if (DEBUG)
                Serial.println("\t Character is comma");

            // Check the current number when a comma is encountered
            if (tempIndex == 0)
            {
                if (DEBUG)
                    Serial.println("\t Number is empty");
                isValid = false; // Empty numbers are invalid
                break;
            }
            temp[tempIndex] = '\0'; // Add null terminator
            if (!isInteger(temp))
            {
                if (DEBUG)
                    Serial.println("\t Not a valid integer");
                isValid = false; // Invalid number
                break;
            }
            tempIndex = 0; // Reset temporary number
            numberCount++; // Increment number counter
        }
        else
        {
            if (DEBUG)
            {
                Serial.println("\t Character is neither a digit nor a comma");
                Serial.print("\t Character is: ");
                Serial.println(currentChar, HEX);
            }
            isValid = false; // Invalid character
            break;
        }
    }

    // Check the last number and ensure proper count
    if (tempIndex > 0)
    {                           // Process the last number
        temp[tempIndex] = '\0'; // Add null terminator
        if (!isInteger(temp))
        {
            isValid = false;
        }
        else
        {
            numberCount++;
        }
    }

    return (isValid && numberCount == 6); // Valid if all checks passed
}

/**
 * @brief Receives and processes a character as part of a message
 *
 * @param receivedChar The character received from serial
 * @param message Buffer to store the message
 * @param index Current index in the message buffer
 */
void receiveMessage(char receivedChar, volatile char *message, volatile int &index)
{
    // Check for end of message (newline)
    if (receivedChar == '\n')
    {
        message[index] = '\0'; // Add null terminator
        if (!DEBUG)
        {
            Serial.println((char *)message);
        }
        else
        {
            // Validate message
            if (validateMessage(message))
            {
                Serial.print("Message is valid: ");
                Serial.println((char *)message);
            }
            else
            {
                Serial.println("invalid");
            }
        }
        // Reset buffer
        index = 0;
    }
    // Check for buffer overflow
    else if (index >= MAX_LENGTH - 1)
    {
        if (DEBUG)
        {
            Serial.println("Error: Message too long, discarded.");
        }
        Serial.println("invalid");
        index = 0; // Reset buffer
    }
    // Store character in buffer
    else
    {
        message[index++] = receivedChar;
    }
}

/**
 * @brief Sends a message/command to the external device
 *
 * @param command The command string to send
 * @param measurementInProgress Reference to the measurement progress flag
 */
void sendMessage(String command, volatile bool &measurementInProgress)
{
    // Send commands to the external device
    command.trim(); // Remove whitespace and control characters
    if (command.length() > 0)
    {
        if (DEBUG)
        {
            Serial.print("Sending: ");
            Serial.println(command);
        }
        Serial1.println(command); // Send command via Serial1

        if (DEBUG)
        {
            Serial.println("Successfully sent.");
        }
    }
    // Handle measurement stop
    if (command == "s0")
    {
        measurementInProgress = false; // Stop measurement
        if (DEBUG)
        {
            Serial.println("Measurement stopped.");
        }
    }
    if (command == "s1")
    {
        measurementInProgress = true; // Start measurement
        if (DEBUG)
        {
            Serial.println("Measurement started.");
        }
    }
    if (command == "info")
    {
        // Handle info command
        if (DEBUG)
        {
            Serial.println("Info command received.");
        }
        Serial.print("OpenBIS code: ");
        Serial.println(O_CODE); // Send OpenBIS code
    }
}
