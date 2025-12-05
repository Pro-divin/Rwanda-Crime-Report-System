/**
 * Dynamic behavior for Report admin form
 * Hides/shows reporter fields based on is_anonymous checkbox
 */

(function($) {
    'use strict';

    $(document).ready(function() {
        // Get the is_anonymous checkbox
        var anonymousCheckbox = $('#id_is_anonymous');
        
        if (anonymousCheckbox.length === 0) {
            return; // Not on the report form
        }

        // Get reporter fields
        var reporterNameField = $('.field-reporter_name');
        var reporterPhoneField = $('.field-reporter_phone');
        var reporterEmailField = $('.field-reporter_email');
        var userField = $('.field-user');

        // Function to toggle reporter fields
        function toggleReporterFields() {
            var isAnonymous = anonymousCheckbox.is(':checked');
            
            if (isAnonymous) {
                // Hide reporter fields
                reporterNameField.hide();
                reporterPhoneField.hide();
                reporterEmailField.hide();
                userField.hide();
                
                // Clear the values (optional, but good for data integrity)
                $('#id_reporter_name').val('');
                $('#id_reporter_phone').val('');
                $('#id_reporter_email').val('');
                $('#id_user').val('');
                
                // Add visual indicator
                $('.field-is_anonymous').css('background-color', '#fff3cd');
                $('.field-is_anonymous label').append(' <strong style="color: #856404;">(Reporter identity will be hidden)</strong>');
            } else {
                // Show reporter fields
                reporterNameField.show();
                reporterPhoneField.show();
                reporterEmailField.show();
                userField.show();
                
                // Remove visual indicator
                $('.field-is_anonymous').css('background-color', '');
                $('.field-is_anonymous label strong').remove();
            }
        }

        // Initial state
        toggleReporterFields();

        // Listen for changes
        anonymousCheckbox.change(function() {
            toggleReporterFields();
        });

        // Add help text
        if ($('.field-is_anonymous .help').length === 0) {
            $('.field-is_anonymous').append(
                '<div class="help" style="margin-top: 5px; color: #666;">' +
                '✓ When checked, reporter name, phone, email, and user will be hidden from public view.' +
                '</div>'
            );
        }
    });
})(django.jQuery);
