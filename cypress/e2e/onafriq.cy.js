it ('Login Test',function(){
    cy.visit('https://www.automationexercise.com/')
    cy.get('.shop-menu > .nav > :nth-child(4) > a').click()
    cy.get('[data-qa="login-email"]').type('qat@mailinator.com')
    cy.get('[data-qa="login-password"]').type('123456')
    cy.get('[data-qa="login-button"]').click()
})
it ('Login Test',function(){
    cy.visit('https://www.automationexercise.com/')
    cy.get('.shop-menu > .nav > :nth-child(4) > a').click()
    cy.get('[data-qa="login-email"]').type('qat@mailinator.com')
    cy.get('[data-qa="login-password"]').type('123456')
    cy.get('[data-qa="login-button"]').click()
    cy.get(':nth-child(1) > .panel-heading > .panel-title > a > .badge > .fa').click()
    cy.get('#Women > .panel-body > ul > :nth-child(1) > a').click()
    cy.get(':nth-child(1) > .panel-heading > .panel-title > a > .badge > .fa').click()
    cy.get('#Women > .panel-body > ul > :nth-child(2) > a').click()
    cy.get(':nth-child(7) > .product-image-wrapper > .single-products > .productinfo > .btn').click()
    cy.get('.modal-footer > .btn').click()
    cy.get(':nth-child(5) > .product-image-wrapper > .single-products > .productinfo > .btn').click()
    cy.get('.shop-menu > .nav > :nth-child(3) > a').click()
    cy.get('.col-sm-6 > .btn').click()
    cy.get('.form-control').type('Order Placed')
    cy.get(':nth-child(7) > .btn').click()
    cy.get('[data-qa="name-on-card"]').type('Test Card')
    cy.get('[data-qa="card-number"]').type('4100 0000 0000')
    cy.get('[data-qa="cvc"]').type('123')
    cy.get('[data-qa="expiry-month"]').type('01')
    cy.get('[data-qa="expiry-year"]').type('1900')
    cy.get('[data-qa="expiry-year"]').click()
    cy.get('[data-qa="pay-button"]').click()





})